from django.db import models
from .user_models import CustomUser

class APIToken(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='api_token',
        verbose_name="Usuario"
    )
    token = models.CharField(max_length=128, unique=True, db_index=True, verbose_name="Token API")
    is_active = models.BooleanField(default=True, verbose_name="Activo")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Token API"
        verbose_name_plural = "Tokens API"

    def __str__(self):
        return f"{self.user.username} - {self.token[:20]}..."
