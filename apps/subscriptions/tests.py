from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from apps.subscriptions.models import Plan, Subscription, SubscriptionStatus, PaymentProof, PaymentStatus, BillingCycle
from apps.subscriptions.services import (
    get_free_plan,
    get_active_subscription,
    get_user_usage_summary,
    can_make_request,
    increment_request_count,
    approve_payment_proof,
    reject_payment_proof
)

User = get_user_model()


class SubscriptionsTestCase(TestCase):
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.admin = User.objects.create_superuser(username='admin', email='admin@example.com', password='adminpassword')
        
        # Seed plans
        self.free_plan = Plan.objects.create(
            code='free', name='Gratuito', monthly_requests=250, price_monthly=0, price_annual=0, is_free=True, display_order=0
        )
        self.plan_10k = Plan.objects.create(
            code='10k', name='10K', monthly_requests=10000, price_monthly=50, price_annual=480, is_free=False, display_order=1
        )

    def test_default_free_subscription(self):
        """Un usuario nuevo obtiene automáticamente el plan Gratuito de 250 peticiones."""
        sub = get_active_subscription(self.user)
        self.assertIsNotNone(sub)
        self.assertEqual(sub.plan.code, 'free')
        self.assertEqual(sub.plan.monthly_requests, 250)

        summary = get_user_usage_summary(self.user)
        self.assertEqual(summary['monthly_requests'], 250)
        self.assertEqual(summary['requests_used'], 0)
        self.assertEqual(summary['requests_remaining'], 250)
        expected_reset = (timezone.now().replace(day=1) + relativedelta(months=1)).date()
        self.assertEqual(summary['reset_date'], expected_reset)

    def test_quota_increment_and_limit(self):
        """Verifica que el incremento de peticiones disminuya el saldo disponible."""
        self.assertTrue(can_make_request(self.user, 200))
        increment_request_count(self.user, 200)

        summary = get_user_usage_summary(self.user)
        self.assertEqual(summary['requests_used'], 200)
        self.assertEqual(summary['requests_remaining'], 50)

        # Tratar de consumir 100 peticiones cuando solo quedan 50
        self.assertFalse(can_make_request(self.user, 100))

    def test_approve_payment_proof_annual(self):
        """Aprobar un comprobante de pago con ciclo Anual activa el nuevo plan por 1 año."""
        proof = PaymentProof.objects.create(
            user=self.user,
            plan=self.plan_10k,
            billing_cycle=BillingCycle.ANNUAL,
            amount=480.00,
            bank_name='BCP',
            reference_number='OP-998877'
        )

        self.assertEqual(proof.status, PaymentStatus.PENDING)

        # Aprobar comprobante
        new_sub = approve_payment_proof(proof, self.admin)
        proof.refresh_from_db()

        self.assertEqual(proof.status, PaymentStatus.APPROVED)
        self.assertEqual(new_sub.status, SubscriptionStatus.ACTIVE)
        self.assertEqual(new_sub.plan.code, '10k')
        self.assertEqual(new_sub.billing_cycle, BillingCycle.ANNUAL)

        # Verificar fecha de vencimiento ~ 1 año
        expected_end = timezone.now() + relativedelta(years=1)
        self.assertAlmostEqual(new_sub.end_date.timestamp(), expected_end.timestamp(), delta=10)

        # Verificar resumen del usuario
        summary = get_user_usage_summary(self.user)
        self.assertEqual(summary['monthly_requests'], 10000)

    def test_reject_payment_proof(self):
        """Rechazar un comprobante actualiza su estado y conserva la suscripción actual."""
        proof = PaymentProof.objects.create(
            user=self.user,
            plan=self.plan_10k,
            billing_cycle=BillingCycle.MONTHLY,
            amount=50.00,
            bank_name='Yape',
            reference_number='OP-001122'
        )

        reject_payment_proof(proof, self.admin, admin_notes="Comprobante ilegible")
        proof.refresh_from_db()

        self.assertEqual(proof.status, PaymentStatus.REJECTED)
        self.assertEqual(proof.admin_notes, "Comprobante ilegible")
        
        # El usuario sigue en el plan Gratuito
        sub = get_active_subscription(self.user)
        self.assertEqual(sub.plan.code, 'free')
