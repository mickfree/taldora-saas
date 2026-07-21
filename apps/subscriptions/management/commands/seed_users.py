import random
import time
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from apps.subscriptions.models import Plan, PaymentProof
from apps.subscriptions.choices import PaymentStatus, BillingCycle

User = get_user_model()

FIRST_NAMES = [
    'Carlos', 'María', 'Juan', 'Ana', 'Luis', 'Sofia', 'Diego', 'Lucía',
    'Mateo', 'Valentina', 'Santiago', 'Camila', 'Leonardo', 'Isabella',
    'Gabriel', 'Valeria', 'Alexander', 'Mariana', 'Daniel', 'Gabriela',
    'Fernando', 'Elena', 'Ricardo', 'Victoria', 'Javier', 'Natalia',
    'Adrian', 'Paula', 'Gonzalo', 'Andrea', 'Manuel', 'Carmen', 'Hugo',
    'Rosa', 'Eduardo', 'Patricia', 'Esteban', 'Claudia', 'Roberto', 'Monica'
]

LAST_NAMES = [
    'García', 'Rodríguez', 'González', 'Fernández', 'López', 'Martínez',
    'Sánchez', 'Pérez', 'Gómez', 'Martín', 'Jiménez', 'Ruiz', 'Hernández',
    'Díaz', 'Moreno', 'Muñoz', 'Álvarez', 'Romero', 'Alonso', 'Gutiérrez',
    'Navarro', 'Torres', 'Domínguez', 'Vázquez', 'Ramos', 'Gil', 'Ramírez',
    'Serrano', 'Blanco', 'Molina', 'Morales', 'Suárez', 'Ortega', 'Delgado'
]

DOMAINS = ['gmail.com', 'outlook.com', 'yahoo.com', 'hotmail.com', 'luckfeed.com', 'deowa.com', 'company.io']


class Command(BaseCommand):
    help = 'Genera cuentas de usuario masivas de prueba (por defecto: 100 cuentas).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Número de usuarios a crear (por defecto: 100)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='Password123!',
            help='Contraseña predeterminada para las cuentas (por defecto: Password123!)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Elimina las cuentas de prueba creadas previamente (usernames que inician con user_ o test_user_)'
        )
        parser.add_argument(
            '--with-payments',
            action='store_true',
            help='Genera automáticamente de 1 a 3 comprobantes de pago por cada usuario creado'
        )

    def handle(self, *args, **options):
        count = options['count']
        raw_password = options['password']
        clear = options['clear']
        with_payments = options['with_payments']

        if clear:
            deleted_count, _ = User.objects.filter(username__istartswith='user_').delete()
            deleted_test, _ = User.objects.filter(username__istartswith='test_user_').delete()
            self.stdout.write(self.style.WARNING(f"Se eliminaron {deleted_count + deleted_test} usuarios de prueba previos."))

        self.stdout.write(self.style.MIGRATE_HEADING(f"Iniciando generación de {count:,} cuentas de usuario..."))
        start_time = time.time()

        hashed_password = make_password(raw_password)
        now = timezone.now()

        existing_usernames = set(User.objects.values_list('username', flat=True))
        users_to_create = []

        for i in range(1, count + 1):
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            domain = random.choice(DOMAINS)

            base_username = f"user_{first.lower()}_{last.lower()}_{i}"
            clean_username = base_username.translate(str.maketrans('áéíóúñÁÉÍÓÚÑ', 'aeiounAEIOUN'))

            if clean_username in existing_usernames:
                clean_username = f"{clean_username}_{random.randint(100, 999)}"
            existing_usernames.add(clean_username)

            email_name = clean_username.replace('user_', '')
            email = f"{email_name}@{domain}"

            user = User(
                username=clean_username,
                first_name=first,
                last_name=last,
                email=email,
                password=hashed_password,
                is_active=True,
                date_joined=now - timedelta(days=random.randint(0, 180))
            )
            users_to_create.append(user)

        created_users = User.objects.bulk_create(users_to_create)
        self.stdout.write(self.style.SUCCESS(f"¡Se crearon exitosamente {len(created_users):,} cuentas de usuario!"))

        if with_payments:
            plans = list(Plan.objects.all())
            if not plans:
                self.stdout.write(self.style.ERROR("No existen planes registrados. Ejecuta 'python manage.py seed_plans' primero."))
            else:
                self.stdout.write("Generando comprobantes de pago para las cuentas creadas...")
                banks = ['BCP', 'BBVA', 'Interbank', 'Scotiabank', 'Yape', 'Plin']
                statuses = [PaymentStatus.PENDING, PaymentStatus.APPROVED, PaymentStatus.REJECTED]
                cycles = [BillingCycle.MONTHLY, BillingCycle.ANNUAL]

                proofs = []
                for user in created_users:
                    num_payments = random.randint(1, 3)
                    for _ in range(num_payments):
                        plan = random.choice(plans)
                        cycle = random.choice(cycles)
                        amount = plan.price_annual if cycle == BillingCycle.ANNUAL else plan.price_monthly
                        random_days = random.randint(0, 90)

                        proof = PaymentProof(
                            user=user,
                            plan=plan,
                            billing_cycle=cycle,
                            amount=amount,
                            bank_name=random.choice(banks),
                            reference_number=f"OP-{random.randint(10000000, 99999999)}",
                            status=random.choice(statuses),
                            created_at=now - timedelta(days=random_days)
                        )
                        proofs.append(proof)

                PaymentProof.objects.bulk_create(proofs)
                self.stdout.write(self.style.SUCCESS(f"Se crearon {len(proofs):,} comprobantes de pago vinculados."))

        elapsed = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(f"Proceso completado en {elapsed:.2f} segundos."))
