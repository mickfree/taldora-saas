from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch
from decimal import Decimal
from .models import ExchangeRate
from .services import get_today_exchange_rate

class ScrapersServicesTestCase(TestCase):
    def setUp(self):
        self.today = timezone.localdate()

    @patch('lambdas.tipo_cambio.lambda_function.lambda_handler')
    def test_get_today_exchange_rate_cache_miss_and_success(self, mock_lambda):
        # Configure mock response from Lambda
        mock_lambda.return_value = {
            "statusCode": 200,
            "body": '{"success": true, "buy_rate": 3.385, "sell_rate": 3.395, "source": "BCRP (20.Jul.26)", "date": "2026-07-21", "warnings": []}'
        }

        # First call: should call lambda and save to DB
        rate = get_today_exchange_rate()
        
        self.assertIsNotNone(rate)
        self.assertEqual(rate.date, self.today)
        self.assertEqual(rate.buy_rate, Decimal('3.3850'))
        self.assertEqual(rate.sell_rate, Decimal('3.3950'))
        self.assertEqual(rate.source, 'BCRP (20.Jul.26)')
        
        # Verify the record exists in DB
        db_rate = ExchangeRate.objects.get(date=self.today)
        self.assertEqual(db_rate.buy_rate, Decimal('3.3850'))
        
        # Verify mock was called once
        mock_lambda.assert_called_once()

    @patch('lambdas.tipo_cambio.lambda_function.lambda_handler')
    def test_get_today_exchange_rate_cache_hit(self, mock_lambda):
        # Pre-populate DB with today's rate
        ExchangeRate.objects.create(
            date=self.today,
            buy_rate=Decimal('3.3500'),
            sell_rate=Decimal('3.3600'),
            source='SBS'
        )
        
        # Call service: should fetch from DB and NOT call Lambda
        rate = get_today_exchange_rate()
        
        self.assertEqual(rate.buy_rate, Decimal('3.3500'))
        self.assertEqual(rate.source, 'SBS')
        mock_lambda.assert_not_called()

    @patch('lambdas.tipo_cambio.lambda_function.lambda_handler')
    def test_get_today_exchange_rate_failure_fallback(self, mock_lambda):
        # Create an old rate in DB to act as fallback
        old_date = self.today - timezone.timedelta(days=1)
        fallback_rate = ExchangeRate.objects.create(
            date=old_date,
            buy_rate=Decimal('3.3000'),
            sell_rate=Decimal('3.3100'),
            source='SBS'
        )
        
        # Configure mock to simulate error in Lambda
        mock_lambda.return_value = {
            "statusCode": 500,
            "body": '{"success": false, "errors": ["Incapsula blocked request"]}'
        }
        
        # Call service: should try lambda, fail, and return old rate
        rate = get_today_exchange_rate()
        
        self.assertEqual(rate, fallback_rate)
        self.assertEqual(rate.buy_rate, Decimal('3.3000'))
