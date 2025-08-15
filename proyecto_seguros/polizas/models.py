from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class TipoSeguro(models.Model):
    """Ej: Seguro de Vida, Seguro de Automóvil, Póliza de Salud."""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    comision_porcentaje = models.DecimalField('Porcentaje de Comisión (%)', max_digits=5, decimal_places=2, default=10.0)

    def __str__(self):
        return self.nombre


class Vehiculo(models.Model):
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehiculos')
    placa = models.CharField("Placa", max_length=10, unique=True, help_text="Placa única del vehículo.")
    marca = models.CharField(max_length=50, blank=True)
    modelo = models.CharField(max_length=50, blank=True)
    ano = models.PositiveIntegerField('Año', blank=True, null=True)
    soat_vencimiento_recordatorio = models.DateField('Recordatorio Vencimiento SOAT', blank=True, null=True, help_text="Fecha de vencimiento del SOAT (incluso si no es de Assecol).")

    class Meta:
        ordering = ['placa']
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"

    def __str__(self):
        return f"{self.placa} ({self.marca} {self.modelo})"

class CompaniaAseguradora(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    # Puedes añadir más campos en el futuro, como NIT, contacto, etc.

    class Meta:
        verbose_name = "Compañía Aseguradora"
        verbose_name_plural = "Compañías Aseguradoras"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
    


    
class Poliza(models.Model):
    # --- Opciones para los campos 'choices' ---
    MODO_PAGO_CHOICES = [
        ('CONTADO', 'De Contado'),
        ('CREDITO', 'A Crédito'),
        ('MENSUAL', 'Pago Mensual'),
    ]
    ESTADO_POLIZA_CHOICES = [
        ('ACTIVA', 'Activa'),
        ('CANCELADA', 'Cancelada'),
        ('VENCIDA', 'Vencida'), # Añadimos un estado para pólizas expiradas
    ]


    ESTADO_CARTERA_CHOICES = [
        ('AL_DIA', 'Al día'),
        ('EN_MORA', 'En mora'),
        ('PAGO_COMPLETO', 'Pago Completo'),
    ]

    # --- Campos de Relación ---
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='polizas')
    compania_aseguradora = models.ForeignKey(CompaniaAseguradora, on_delete=models.PROTECT, related_name='polizas')
    tipo_seguro = models.ForeignKey(TipoSeguro, on_delete=models.PROTECT, related_name='polizas')

    # --- Campos de Información Básica ---
    numero_poliza = models.CharField(max_length=50, unique=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    poliza_pdf = models.FileField(upload_to='polizas_pdf/', blank=True, null=True)

    # --- Campos Financieros y de Comisión ---
    prima_total = models.DecimalField('Valor Prima Total', max_digits=12, decimal_places=2)

    #---Se relaciona con un vehiculo solo si la poliza es d+para un vehiculo
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.SET_NULL, null=True, blank=True, related_name='polizas', help_text="Opcional: Llenar solo si la póliza es para un vehículo.")

    # --- Campos de Modalidad de Pago ---
    modo_pago = models.CharField('Modalidad de Pago', max_length=10, choices=MODO_PAGO_CHOICES, default='CONTADO')
    plazo_meses = models.PositiveIntegerField('Plazo en Meses', default=12, help_text="Relevante para pago a Crédito o Mensual")
    # entidad_financiera lo añadiremos después si es necesario para simplificar ahora
    estado_cartera = models.CharField('Estado de Cartera', max_length=15, choices=ESTADO_CARTERA_CHOICES, default='AL_DIA')     
    # --- Campos de Estado y Cancelación ---
    estado = models.CharField('Estado de la Póliza', max_length=10, choices=ESTADO_POLIZA_CHOICES, default='ACTIVA')
    fecha_cancelacion = models.DateField(blank=True, null=True)
    motivo_cancelacion = models.TextField(blank=True)

    monto_devolucion = models.DecimalField('Monto a Devolver', max_digits=12, decimal_places=2, null=True, blank=True, help_text="Calculado al momento de la cancelación.")
    comision_devuelta = models.DecimalField('Comisión a Devolver', max_digits=12, decimal_places=2, null=True, blank=True, help_text="Comisión que Assecol retorna, calculada al cancelar.")

    class Meta:
        ordering = ['-fecha_fin']

    def __str__(self):
        return f"Póliza {self.numero_poliza} - {self.cliente.username}"

    @property
    def valor_comision(self):
        """Calcula el valor de la comisión buscando el % en el Tipo de Seguro."""
        if self.prima_total and self.tipo_seguro.comision_porcentaje:
            return (self.prima_total * self.tipo_seguro.comision_porcentaje) / 100
        return 0
    

    def calcular_prorrateo_cancelacion(self):
        """
        Calcula la devolución al cliente y la comisión a retornar por Assecol
        para pólizas pagadas de contado.
        """
        if not self.modo_pago == 'CONTADO' or not self.fecha_cancelacion:
            return None, None # No aplica si no es de contado o no está cancelada

        # 1. Calcular días totales y días activos
        dias_totales_poliza = (self.fecha_fin - self.fecha_inicio).days
        if dias_totales_poliza <= 0:
            return 0, 0

        dias_activos = (self.fecha_cancelacion - self.fecha_inicio).days

        # 2. Calcular costo diario
        costo_diario_prima = self.prima_total / dias_totales_poliza
        costo_diario_comision = self.valor_comision / dias_totales_poliza

        # 3. Calcular montos consumidos
        prima_consumida = costo_diario_prima * dias_activos
        comision_ganada = costo_diario_comision * dias_activos

        # 4. Calcular montos a devolver
        monto_a_devolver_cliente = self.prima_total - prima_consumida
        comision_a_devolver_assecol = self.valor_comision - comision_ganada

        # Redondeamos a 2 decimales para evitar problemas
        return round(monto_a_devolver_cliente, 2), round(comision_a_devolver_assecol, 2)
    

