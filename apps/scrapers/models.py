from django.db import models

class ExchangeRate(models.Model):
    date = models.DateField(unique=True, db_index=True, verbose_name="Fecha")
    buy_rate = models.DecimalField(max_digits=6, decimal_places=4, verbose_name="Precio Compra (S/)")
    sell_rate = models.DecimalField(max_digits=6, decimal_places=4, verbose_name="Precio Venta (S/)")
    source = models.CharField(max_length=50, verbose_name="Origen de Data")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Fecha de Modificación")

    class Meta:
        verbose_name = "Tipo de Cambio"
        verbose_name_plural = "Tipos de Cambio"
        ordering = ['-date']

    def __str__(self):
        return f"{self.date}: Compra: {self.buy_rate} | Venta: {self.sell_rate} ({self.source})"
