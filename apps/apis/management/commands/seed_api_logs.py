import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.apis.models import ApiRequestLog

User = get_user_model()

class Command(BaseCommand):
    help = 'Genera logs de peticiones API de prueba para el usuario principal o especificado'

    SERVICES = [
        ('sunat_ruc', 'SUNAT RUC', ['20601234567', '20100070970', '20512345678', '10456789012']),
        ('reniec_dni', 'RENIEC DNI', ['72819203', '45892104', '09812345', '71239401']),
        ('sunarp_placa', 'Vehicular SUNARP', ['ABC-123', 'XYZ-987', 'B1C-456', 'M1P-789']),
        ('tipo_cambio', 'Tipo de Cambio USD', ['Hoy', '2026-07-20', '2026-07-19']),
    ]

    NODES = [
        'AWS Lambda us-east-1',
        'AWS Scraper-Node-01',
        'AWS Scraper-Node-02',
        'Scraper Edge Lima-01'
    ]

    STATUS_CHOICES = [200, 200, 200, 200, 200, 200, 200, 404, 500, 429]

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Nombre del usuario objetivo')
        parser.add_argument('--count', type=int, default=30, help='Cantidad de logs a generar')

    def handle(self, *args, **options):
        username = options.get('username')
        count = options.get('count', 30)

        if username:
            user = User.objects.filter(username=username).first()
        else:
            user = User.objects.first()

        if not user:
            self.stdout.write(self.style.ERROR("No se encontró ningún usuario para asociar los logs."))
            return

        self.stdout.write(f"Generando {count} logs de prueba para el usuario {user.username}...")

        now = timezone.now()
        created_count = 0
        STATUS_CHOICES = [200, 200, 200, 200, 200, 200, 200, 404, 500, 429]
        for i in range(count):
            service_code, service_name, sample_params = random.choice(self.SERVICES)
            query_param = random.choice(sample_params)
            status_code = random.choice(STATUS_CHOICES)
            latency_ms = random.randint(80, 850) if status_code == 200 else random.randint(120, 2100)
            scraper_node = random.choice(self.NODES)
            
            # Distribuir fechas en los últimos 14 días
            random_days = random.randint(0, 13)
            random_hours = random.randint(0, 23)
            random_minutes = random.randint(0, 59)
            created_at = now - timedelta(days=random_days, hours=random_hours, minutes=random_minutes)

            log = ApiRequestLog.objects.create(
                user=user,
                service_code=service_code,
                service_name=service_name,
                query_param=query_param,
                status_code=status_code,
                latency_ms=latency_ms,
                scraper_node=scraper_node
            )
            # Sobrescribir created_at (auto_now_add lo asigna al guardar, pero podemos usar update)
            ApiRequestLog.objects.filter(id=log.id).update(created_at=created_at)
            created_count += 1

        self.stdout.write(self.style.SUCCESS(f"¡Se generaron {created_count} logs de peticiones API con éxito!"))
