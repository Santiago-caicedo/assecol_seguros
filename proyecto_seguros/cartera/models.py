# cartera/models.py
from django.db import models
from polizas.models import Poliza

class Cuota(models.Model):
    ESTADO_CUOTA_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('PAGADA', 'Pagada'),
        ('EN_MORA', 'En Mora'),
    ]
    poliza = models.ForeignKey(Poliza, on_delete=models.CASCADE, related_name='cuotas')
    numero_cuota = models.PositiveIntegerField()
    fecha_vencimiento = models.DateField()
    monto_cuota = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=10, choices=ESTADO_CUOTA_CHOICES, default='PENDIENTE')

    class Meta:
        unique_together = ('poliza', 'numero_cuota') # No puede haber dos "cuota 1" para la misma póliza
        ordering = ['numero_cuota']

    def __str__(self):
        return f"Cuota {self.numero_cuota} de {self.poliza.numero_poliza}"

class Pago(models.Model):
    poliza = models.ForeignKey(Poliza, on_delete=models.CASCADE, related_name='pagos')
    # El pago puede estar asociado a una cuota específica (para pagos mensuales) o no (para pago de contado)
    cuota = models.ForeignKey(Cuota, on_delete=models.SET_NULL, null=True, blank=True, related_name='pagos')
    fecha_pago = models.DateField()
    monto_pagado = models.DecimalField(max_digits=12, decimal_places=2)
    comprobante = models.FileField(upload_to='comprobantes/', blank=True, null=True)
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ['-fecha_pago']

    def __str__(self):
        return f"Pago de {self.monto_pagado} para {self.poliza.numero_poliza} el {self.fecha_pago}"