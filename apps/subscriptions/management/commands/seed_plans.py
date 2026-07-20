from django.core.management.base import BaseCommand
from apps.subscriptions.models import Plan


class Command(BaseCommand):
    help = 'Siembra o actualiza los 5 planes de suscripción predeterminados'

    PLANS = [
        {
            'code': 'free',
            'name': 'Gratuito',
            'monthly_requests': 250,
            'price_monthly': 0.00,
            'price_annual': 0.00,
            'is_free': True,
            'display_order': 0,
        },
        {
            'code': '10k',
            'name': '10K',
            'monthly_requests': 10000,
            'price_monthly': 50.00,
            'price_annual': 480.00,
            'is_free': False,
            'display_order': 1,
        },
        {
            'code': '30k',
            'name': '30K',
            'monthly_requests': 30000,
            'price_monthly': 100.00,
            'price_annual': 960.00,
            'is_free': False,
            'display_order': 2,
        },
        {
            'code': '50k',
            'name': '50K',
            'monthly_requests': 50000,
            'price_monthly': 150.00,
            'price_annual': 1440.00,
            'is_free': False,
            'display_order': 3,
        },
        {
            'code': '100k',
            'name': '100K',
            'monthly_requests': 100000,
            'price_monthly': 250.00,
            'price_annual': 2400.00,
            'is_free': False,
            'display_order': 4,
        },
    ]

    def handle(self, *args, **options):
        self.stdout.write("Sembrando planes de suscripción...")
        for data in self.PLANS:
            plan, created = Plan.objects.update_or_create(
                code=data['code'],
                defaults=data
            )
            action = "Creado" if created else "Actualizado"
            self.stdout.write(self.style.SUCCESS(f" - [{action}] {plan.name} ({plan.monthly_requests:,} req/mes)"))
        self.stdout.write(self.style.SUCCESS("¡Planes sembrados exitosamente!"))
