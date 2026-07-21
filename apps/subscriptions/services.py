from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.db import transaction
from .models import Plan, Subscription, SubscriptionStatus, PaymentProof, PaymentStatus, MonthlyUsage, BillingCycle


def get_free_plan():
    """Obtiene o crea el plan Gratuito por defecto."""
    plan, _ = Plan.objects.get_or_create(
        code='free',
        defaults={
            'name': 'Gratuito',
            'monthly_requests': 250,
            'price_monthly': 0.00,
            'price_annual': 0.00,
            'is_free': True,
            'is_active': True,
            'display_order': 0
        }
    )
    return plan


def get_active_subscription(user):
    """
    Retorna la suscripción activa del usuario.
    Si su suscripción de pago venció, la actualiza a VENCIDA y le asigna el plan Gratuito.
    """
    now = timezone.now()
    active_sub = Subscription.objects.filter(
        user=user,
        status=SubscriptionStatus.ACTIVE
    ).select_related('plan').first()

    if active_sub:
        if active_sub.end_date and active_sub.end_date < now:
            active_sub.status = SubscriptionStatus.EXPIRED
            active_sub.save(update_fields=['status', 'updated_at'])
            active_sub = None

    if not active_sub:
        free_plan = get_free_plan()
        active_sub, _ = Subscription.objects.get_or_create(
            user=user,
            plan=free_plan,
            status=SubscriptionStatus.ACTIVE,
            defaults={
                'billing_cycle': BillingCycle.MONTHLY,
                'start_date': now,
                'end_date': None
            }
        )

    return active_sub


def get_current_year_month():
    """Retorna la cadena YYYY-MM actual."""
    return timezone.now().strftime("%Y-%m")


def get_current_monthly_usage(user):
    """Obtiene o inicializa el objeto MonthlyUsage para el mes actual."""
    year_month = get_current_year_month()
    usage, _ = MonthlyUsage.objects.get_or_create(
        user=user,
        year_month=year_month,
        defaults={'request_count': 0}
    )
    return usage


def get_user_usage_summary(user):
    """
    Retorna un diccionario con el resumen de suscripción y uso del mes:
    - plan_name
    - billing_cycle
    - monthly_requests
    - requests_used
    - requests_remaining
    - percentage_used
    - end_date
    """
    sub = get_active_subscription(user)
    usage = get_current_monthly_usage(user)

    total_limit = sub.plan.monthly_requests
    used = usage.request_count
    remaining = max(0, total_limit - used)
    percentage = round((used / total_limit * 100), 1) if total_limit > 0 else 100.0

    return {
        'subscription': sub,
        'plan': sub.plan,
        'plan_name': sub.plan.name,
        'billing_cycle': sub.get_billing_cycle_display(),
        'monthly_requests': total_limit,
        'requests_used': used,
        'requests_remaining': remaining,
        'percentage_used': min(100.0, percentage),
        'end_date': sub.end_date,
        'is_free': sub.plan.is_free,
    }


def can_make_request(user, amount=1):
    """Verifica si el usuario tiene saldo de peticiones disponible para el mes actual."""
    summary = get_user_usage_summary(user)
    return summary['requests_remaining'] >= amount


def increment_request_count(user, amount=1):
    """Incrementa las peticiones realizadas en el mes actual."""
    usage = get_current_monthly_usage(user)
    usage.request_count += amount
    usage.save(update_fields=['request_count', 'updated_at'])
    return usage.request_count


@transaction.atomic
def approve_payment_proof(payment_proof, admin_user=None):
    """
    Aprueba un comprobante de pago:
    1. Desactiva suscripciones activas previas.
    2. Crea una nueva suscripción activa con el plan y ciclo solicitados.
    3. Marca el comprobante como Aprobado.
    """
    active_sub = Subscription.objects.filter(
        user=payment_proof.user,
        status=SubscriptionStatus.ACTIVE
    ).select_related('plan').first()

    # Si ya tiene una suscripción activa para este mismo plan, devolverla
    if active_sub and active_sub.plan_id == payment_proof.plan_id and not active_sub.plan.is_free:
        if payment_proof.status != PaymentStatus.APPROVED:
            payment_proof.status = PaymentStatus.APPROVED
            if admin_user:
                payment_proof.reviewed_by = admin_user
            payment_proof.reviewed_at = timezone.now()
            payment_proof.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
        return active_sub

    now = timezone.now()
    
    # 1. Expirar suscripciones activas previas
    Subscription.objects.filter(
        user=payment_proof.user,
        status=SubscriptionStatus.ACTIVE
    ).update(status=SubscriptionStatus.EXPIRED)

    # 2. Calcular fecha fin
    if payment_proof.billing_cycle == BillingCycle.ANNUAL:
        end_date = now + relativedelta(years=1)
    else:
        end_date = now + relativedelta(months=1)

    # 3. Crear nueva suscripción
    new_sub = Subscription.objects.create(
        user=payment_proof.user,
        plan=payment_proof.plan,
        billing_cycle=payment_proof.billing_cycle,
        status=SubscriptionStatus.ACTIVE,
        start_date=now,
        end_date=end_date
    )

    # 4. Actualizar estado del comprobante
    payment_proof.status = PaymentStatus.APPROVED
    if admin_user:
        payment_proof.reviewed_by = admin_user
    payment_proof.reviewed_at = now
    payment_proof.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])

    return new_sub


@transaction.atomic
def reject_payment_proof(payment_proof, admin_user, admin_notes=None):
    """Rechaza un comprobante de pago."""
    payment_proof.status = PaymentStatus.REJECTED
    payment_proof.reviewed_by = admin_user
    payment_proof.reviewed_at = timezone.now()
    if admin_notes:
        payment_proof.admin_notes = admin_notes
    payment_proof.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'admin_notes'])
    return payment_proof
