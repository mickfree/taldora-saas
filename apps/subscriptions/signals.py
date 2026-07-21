from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PaymentProof, PaymentStatus
from .services import approve_payment_proof


@receiver(post_save, sender=PaymentProof)
def handle_payment_proof_post_save(sender, instance, created, **kwargs):
    """
    Escucha la señal post_save de PaymentProof.
    Si el comprobante está en estado Aprobado, activa automáticamente la suscripción correspondiente del usuario.
    """
    if instance.status == PaymentStatus.APPROVED:
        approve_payment_proof(instance)
