from django.db import models
from django.conf import settings
from .managers import ApiRequestLogManager

class ApiRequestLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='api_request_logs',
        verbose_name="Usuario"
    )

    objects = ApiRequestLogManager()


    service_code = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="Código del Servicio"
    )
    service_name = models.CharField(
        max_length=100,
        verbose_name="Nombre del Servicio"
    )
    query_param = models.CharField(
        max_length=255,
        blank=True,
        default='',
        verbose_name="Parámetro Consultado"
    )
    status_code = models.PositiveIntegerField(
        default=200,
        db_index=True,
        verbose_name="Código de Estado HTTP"
    )
    latency_ms = models.PositiveIntegerField(
        default=0,
        verbose_name="Latencia (ms)"
    )
    scraper_node = models.CharField(
        max_length=100,
        default='AWS Lambda us-east-1',
        verbose_name="Nodo Scraper"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="Fecha de Petición"
    )

    class Meta:
        verbose_name = "Log de Petición API"
        verbose_name_plural = "Logs de Peticiones API"
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.status_code}] {self.service_name} - {self.user.username} ({self.created_at.strftime('%Y-%m-%d %H:%M:%S')})"

    @property
    def status_label(self):
        labels = {
            200: 'OK',
            400: 'Bad Request',
            401: 'Unauthorized',
            403: 'Forbidden',
            404: 'Not Found',
            429: 'Quota Exceeded',
            500: 'Server Error',
            503: 'Service Unavailable',
        }
        return labels.get(self.status_code, 'Error')

    @property
    def formatted_latency(self):
        if self.latency_ms >= 1000:
            return f"{round(self.latency_ms / 1000, 2)}s"
        return f"{self.latency_ms}ms"
