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


class RUCData(models.Model):
    ruc = models.CharField(max_length=11, unique=True, db_index=True, verbose_name="RUC")
    razon_social = models.CharField(max_length=255, verbose_name="Razón Social / Nombre")
    estado = models.CharField(max_length=50, default="ACTIVO", verbose_name="Estado")
    condicion = models.CharField(max_length=50, default="HABIDO", verbose_name="Condición")
    direccion = models.CharField(max_length=255, blank=True, default="", verbose_name="Dirección Fiscal")
    departamento = models.CharField(max_length=100, blank=True, default="", verbose_name="Departamento")
    provincia = models.CharField(max_length=100, blank=True, default="", verbose_name="Provincia")
    distrito = models.CharField(max_length=100, blank=True, default="", verbose_name="Distrito")
    ubigeo = models.CharField(max_length=10, blank=True, default="", verbose_name="Ubigeo")
    es_agente_retencion = models.BooleanField(default=False, verbose_name="Es Agente de Retención")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Consulta Inicial")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        verbose_name = "Consulta RUC SUNAT"
        verbose_name_plural = "Consultas RUC SUNAT"
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.ruc} - {self.razon_social} ({self.estado})"

class SUNARPData(models.Model):
    placa = models.CharField(max_length=15, unique=True, db_index=True, verbose_name="Placa Vehicular")
    numero_serie = models.CharField(max_length=100, blank=True, default="-", verbose_name="N° Serie")
    numero_vin = models.CharField(max_length=100, blank=True, default="-", verbose_name="N° VIN")
    numero_motor = models.CharField(max_length=100, blank=True, default="-", verbose_name="N° Motor")
    color = models.CharField(max_length=100, blank=True, default="-", verbose_name="Color")
    marca = models.CharField(max_length=100, blank=True, default="-", verbose_name="Marca")
    modelo = models.CharField(max_length=100, blank=True, default="-", verbose_name="Modelo")
    placa_vigente = models.CharField(max_length=20, blank=True, default="-", verbose_name="Placa Vigente")
    placa_anterior = models.CharField(max_length=20, blank=True, default="NINGUNA", verbose_name="Placa Anterior")
    estado = models.CharField(max_length=100, default="EN CIRCULACION", verbose_name="Estado")
    anotaciones = models.CharField(max_length=255, default="NINGUNA", verbose_name="Anotaciones")
    sede = models.CharField(max_length=100, blank=True, default="-", verbose_name="Sede")
    anio_modelo = models.CharField(max_length=10, blank=True, default="-", verbose_name="Año de Modelo")
    propietarios = models.TextField(blank=True, default="", verbose_name="Propietario(s)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Consulta Inicial")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        verbose_name = "Consulta Vehicular SUNARP"
        verbose_name_plural = "Consultas Vehiculares SUNARP"
        ordering = ['-updated_at']

    def __str__(self):
        return f"SUNARP Placa {self.placa} - {self.marca} {self.modelo} ({self.propietarios})"



