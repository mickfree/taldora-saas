import random
import time
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.subscriptions.models import Plan, PaymentProof
from apps.subscriptions.choices import PaymentStatus, BillingCycle

User = get_user_model()


class Command(BaseCommand):
    help = 'Genera comprobantes de pago masivos para pruebas de estrés y paginación (ej: 10,000 registros).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10000,
            help='Número de comprobantes de pago a crear (por defecto: 10000)'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Username del usuario al que se le asignarán los comprobantes (por defecto: primer usuario activo o superusuario)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Elimina los comprobantes de pago existentes antes de sembrar los nuevos'
        )

    def handle(self, *args, **options):
        count = options['count']
        username = options.get('username')
        clear = options['clear']

        # 1. Obtener o verificar usuario
        if username:
            user = User.objects.filter(username=username).first()
            if not user:
                self.stderr.write(self.style.ERROR(f"Usuario '{username}' no encontrado."))
                return
        else:
            user = User.objects.first()
            if not user:
                # Crear un usuario de prueba si no existe ninguno
                user = User.objects.create_user(
                    username='demo_stress',
                    email='demo_stress@example.com',
                    password='Password123!'
                )
                self.stdout.write(self.style.WARNING("No había usuarios. Se creó el usuario demo 'demo_stress'."))

        # 2. Obtener planes disponibles
        plans = list(Plan.objects.all())
        if not plans:
            self.stderr.write(self.style.ERROR("No existen planes registrados. Ejecuta 'python manage.py seed_plans' primero."))
            return

        # 3. Limpiar registros anteriores si se solicita
        if clear:
            deleted_count, _ = PaymentProof.objects.filter(user=user).delete()
            self.stdout.write(self.style.WARNING(f"Se eliminaron {deleted_count} comprobantes previos para el usuario {user.username}."))

        self.stdout.write(self.style.MIGRATE_HEADING(f"Iniciando generación de {count:,} comprobantes de pago para '{user.username}'..."))
        start_time = time.time()

        banks = ['BCP', 'BBVA', 'Interbank', 'Scotiabank', 'Yape', 'Plin', 'Banco de la Nación']
        statuses = [PaymentStatus.PENDING, PaymentStatus.APPROVED, PaymentStatus.REJECTED]
        cycles = [BillingCycle.MONTHLY, BillingCycle.ANNUAL]

        now = timezone.now()
        proofs = []
        batch_size = 2000

        for i in range(1, count + 1):
            plan = random.choice(plans)
            cycle = random.choice(cycles)
            amount = plan.price_annual if cycle == BillingCycle.ANNUAL else plan.price_monthly
            
            # Generar fecha aleatoria dentro de los últimos 180 días
            random_days = random.randint(0, 180)
            random_minutes = random.randint(0, 1440)
            created_at = now - timedelta(days=random_days, minutes=random_minutes)

            proof = PaymentProof(
                user=user,
                plan=plan,
                billing_cycle=cycle,
                amount=amount,
                bank_name=random.choice(banks),
                reference_number=f"OP-{random.randint(10000000, 99999999)}",
                status=random.choice(statuses),
                admin_notes="Generado automáticamente para prueba de estrés" if i % 5 == 0 else None,
                created_at=created_at
            )
            proofs.append(proof)

            # Insertar en lotes de 2000
            if len(proofs) >= batch_size:
                PaymentProof.objects.bulk_create(proofs)
                self.stdout.write(f" -> Insertados {i:,} / {count:,} comprobantes...")
                proofs = []

        # Insertar los restantes
        if proofs:
            PaymentProof.objects.bulk_create(proofs)

        elapsed = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS(
                f"\n¡Éxito! Se crearon {count:,} comprobantes de pago para '{user.username}' en {elapsed:.2f} segundos."
            )
        )
