from django.db import models
from django.conf import settings
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from apps.subscriptions.choices import BillingCycle, SubscriptionStatus, PaymentStatus


class Plan(models.Model):
    code = models.CharField(max_length=20, unique=True, verbose_name="Código del Plan")
    name = models.CharField(max_length=50, verbose_name="Nombre del Plan")
    monthly_requests = models.PositiveIntegerField(default=250, verbose_name="Peticiones Mensuales")
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Precio Mensual (PEN)")
    price_annual = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Precio Anual (PEN)")
    is_free = models.BooleanField(default=False, verbose_name="Es Gratuito")
    is_active = models.BooleanField(default=True, verbose_name="Está Activo")
    display_order = models.IntegerField(default=0, verbose_name="Orden de Despliegue")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Plan de Suscripción"
        verbose_name_plural = "Planes de Suscripción"
        ordering = ['display_order', 'price_monthly']

    def __str__(self):
        return f"{self.name} ({self.monthly_requests:,} req/mes)"

    @property
    def effective_monthly_annual_price(self):
        """Calcula el costo equivalente por mes en el pago anual."""
        if self.price_annual > 0:
            return round(self.price_annual / 12, 2)
        return round(self.price_monthly, 2)

    @property
    def cost_per_request(self):
        """Costo aproximado por petición en el plan mensual."""
        if self.monthly_requests > 0 and self.price_monthly > 0:
            return round(self.price_monthly / self.monthly_requests, 4)
        return 0.0000


class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions', verbose_name="Usuario")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions', verbose_name="Plan")
    billing_cycle = models.CharField(max_length=10, choices=BillingCycle.choices, default=BillingCycle.MONTHLY, verbose_name="Ciclo de Facturación")
    status = models.CharField(max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.ACTIVE, verbose_name="Estado")
    start_date = models.DateTimeField(default=timezone.now, verbose_name="Fecha de Inicio")
    end_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Vencimiento")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Suscripción"
        verbose_name_plural = "Suscripciones"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.plan.name} ({self.get_status_display()})"

    @property
    def is_valid(self):
        if self.status != SubscriptionStatus.ACTIVE:
            return False
        if self.end_date is not None and self.end_date < timezone.now():
            return False
        return True


class PaymentProof(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_proofs', verbose_name="Usuario")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='payment_proofs', verbose_name="Plan Solicitado")
    billing_cycle = models.CharField(max_length=10, choices=BillingCycle.choices, default=BillingCycle.MONTHLY, verbose_name="Ciclo Solicitado")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Monto Depositado (PEN)")
    bank_name = models.CharField(max_length=100, verbose_name="Banco / Entidad")
    reference_number = models.CharField(max_length=100, verbose_name="N° de Operación / Referencia")
    proof_file = models.FileField(upload_to='payment_proofs/%Y/%m/', null=True, blank=True, verbose_name="Comprobante Adjunto")
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING, verbose_name="Estado")
    admin_notes = models.TextField(blank=True, null=True, verbose_name="Notas del Administrador")
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_payment_proofs', verbose_name="Revisado Por")
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de Revisión")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Envío")

    class Meta:
        verbose_name = "Comprobante de Pago"
        verbose_name_plural = "Comprobantes de Pago"
        ordering = ['-created_at']

    def __str__(self):
        return f"Comprobante #{self.id} - {self.user.username} ({self.plan.name})"


class MonthlyUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='monthly_usages', verbose_name="Usuario")
    year_month = models.CharField(max_length=7, db_index=True, verbose_name="Año-Mes (YYYY-MM)")
    request_count = models.PositiveIntegerField(default=0, verbose_name="Peticiones Realizadas")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Consumo Mensual"
        verbose_name_plural = "Consumos Mensuales"
        unique_together = ('user', 'year_month')
        ordering = ['-year_month']

    def __str__(self):
        return f"{self.user.username} - {self.year_month}: {self.request_count} reqs"
