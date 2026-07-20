import logging
from allauth.account.adapter import DefaultAccountAdapter
from celery import shared_task
from django.core.mail import EmailMultiAlternatives

# Configure logger
logger = logging.getLogger(__name__)

@shared_task
def send_celery_email(subject, body, from_email, to, html_message=None):
    logger.info(f"Iniciando envío de correo en segundo plano. Asunto: {subject} | Destinatario: {to}")
    try:
        msg = EmailMultiAlternatives(subject, body, from_email, to)
        if html_message:
            msg.attach_alternative(html_message, "text/html")
        msg.send()
        logger.info(f"Correo enviado exitosamente a: {to}")
    except Exception as e:
        logger.error(f"Error al enviar correo a {to}: {str(e)}")
        raise e

class CeleryAccountAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        msg = self.render_mail(template_prefix, email, context)
        send_celery_email.delay(
            subject=msg.subject,
            body=msg.body,
            from_email=msg.from_email,
            to=msg.to,
            html_message=getattr(msg, 'html', None)
        )
