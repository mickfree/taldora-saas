from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from apps.users.models import CustomUser, APIToken
from apps.scrapers.models import ExchangeRate
from apps.subscriptions.models import Plan, Subscription, SubscriptionStatus, MonthlyUsage
from apps.subscriptions.services import get_free_plan

class PublicAPITests(TestCase):
    def setUp(self):
        # 1. Create client and users
        self.client = Client()
        self.user = CustomUser.objects.create_user(username="testuser", password="password123")
        
        # 2. Get or create free plan and activate subscription
        self.free_plan = get_free_plan()
        self.subscription = Subscription.objects.create(
            user=self.user,
            plan=self.free_plan,
            status=SubscriptionStatus.ACTIVE,
            start_date=timezone.now(),
            end_date=None
        )
        
        # 3. Initialize usage record
        self.usage = MonthlyUsage.objects.create(
            user=self.user,
            year_month=timezone.now().strftime("%Y-%m"),
            request_count=0
        )
        
        # 4. Generate token
        self.api_token = APIToken.objects.create(
            user=self.user,
            token="taldora_sk_live_1234567890abcdef"
        )
        
        # 5. Populate cache database with a rate
        self.exchange_rate = ExchangeRate.objects.create(
            date=timezone.localdate(),
            buy_rate=Decimal('3.3900'),
            sell_rate=Decimal('3.4000'),
            source='BCRP'
        )

    def test_public_api_tipo_cambio_bearer_header(self):
        url = reverse('api_tipo_cambio')
        headers = {'HTTP_AUTHORIZATION': f"Bearer {self.api_token.token}"}
        
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['compra'], 3.39)
        self.assertEqual(data['venta'], 3.4)
        self.assertEqual(data['fuente'], 'BCRP')
        
        # Verify usage count was incremented
        self.usage.refresh_from_db()
        self.assertEqual(self.usage.request_count, 1)

    def test_public_api_tipo_cambio_custom_header(self):
        url = reverse('api_tipo_cambio')
        # Django maps custom headers as HTTP_<UPPERCASE_NAME>
        headers = {'HTTP_X_API_KEY': self.api_token.token}
        
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['compra'], 3.39)
        
        self.usage.refresh_from_db()
        self.assertEqual(self.usage.request_count, 1)

    def test_public_api_tipo_cambio_query_parameter(self):
        url = f"{reverse('api_tipo_cambio')}?api_key={self.api_token.token}"
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['compra'], 3.39)
        
        self.usage.refresh_from_db()
        self.assertEqual(self.usage.request_count, 1)

    def test_public_api_tipo_cambio_invalid_token(self):
        url = reverse('api_tipo_cambio')
        headers = {'HTTP_AUTHORIZATION': "Bearer invalid_token_here"}
        
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, 401)
        
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], "Token de API inválido o inactivo.")
        
        # Usage must not change
        self.usage.refresh_from_db()
        self.assertEqual(self.usage.request_count, 0)

    def test_public_api_tipo_cambio_missing_token(self):
        url = reverse('api_tipo_cambio')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)
        
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn("No se proporcionó un token de API", data['error'])

    def test_public_api_tipo_cambio_rate_limit_exceeded(self):
        # Exceed free limit (250 requests)
        self.usage.request_count = 250
        self.usage.save()
        
        url = reverse('api_tipo_cambio')
        headers = {'HTTP_AUTHORIZATION': f"Bearer {self.api_token.token}"}
        
        response = self.client.get(url, **headers)
        self.assertEqual(response.status_code, 429)
        
        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['error'], "Límite de peticiones de tu plan excedido para el mes actual.")
        
        # Usage remains at 250
        self.usage.refresh_from_db()
        self.assertEqual(self.usage.request_count, 250)
