from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from apps.users.models import CustomUser, APIToken
from apps.subscriptions.models import Subscription, SubscriptionStatus, MonthlyUsage
from apps.subscriptions.services import get_free_plan

class UserTokenAPITestCase(TestCase):
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

    def test_api_token_model_creation(self):
        token_count = APIToken.objects.count()
        print(token_count)
        self.assertEqual(token_count, 1)
        self.assertEqual(self.api_token.user, self.user)
        self.assertTrue(self.api_token.token.startswith("taldora_sk_live_"))

    def test_token_regeneration_view_authenticated(self):
        self.client.login(username="testuser", password="password123")
        old_token_str = self.api_token.token
        
        response = self.client.post(reverse('regenerate_token'))
        self.assertEqual(response.status_code, 200)
        
        # Verify token was updated in DB
        self.api_token.refresh_from_db()
        self.assertNotEqual(self.api_token.token, old_token_str)
        self.assertTrue(self.api_token.token.startswith("taldora_sk_live_"))
        
        # Verify HTMX partial content is returned containing the new token
        self.assertContains(response, self.api_token.token)

    def test_token_regeneration_view_unauthenticated(self):
        response = self.client.post(reverse('regenerate_token'))
        # Should redirect to login since @login_required is used
        self.assertEqual(response.status_code, 302)
