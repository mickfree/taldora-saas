from django.db import models


class BillingCycle(models.TextChoices):
    MONTHLY = 'MONTHLY', 'Mensual'
    ANNUAL = 'ANNUAL', 'Anual'


class SubscriptionStatus(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Activa'
    EXPIRED = 'EXPIRED', 'Vencida'
    CANCELLED = 'CANCELLED', 'Cancelada'


class PaymentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pendiente de Revisión'
    APPROVED = 'APPROVED', 'Aprobado'
    REJECTED = 'REJECTED', 'Rechazado'
