from django.db import models
from polizas.models import Poliza

class Siniestro(models.Model):
    # --- Opciones para los campos 'choices' ---
    TIPO_SINIESTRO_CHOICES = [
        ('RESPONSABILIDAD_CIVIL', 'Responsabilidad Civil Extracontractual'),
        ('DANOS_PROPIOS', 'Daños Propios'),
    ]

    SUBTIPO_RC_CHOICES = [
        ('SOLO_DANOS', 'Solo Daños'),
        ('DANOS_LESIONES_1', 'Daños y Lesiones a 1 Persona'),
        ('LESIONES_1', 'Lesiones a 1 Persona'),
        ('LESIONES_2_MAS', 'Lesiones a 2 o más Personas'),
        ('DANOS_MUERTE_1', 'Daños y Muerte a 1 Persona'),
        ('DANOS_MUERTE_2_MAS', 'Daños y Muerte a 2 o más Personas'),
        ('MUERTE_1', 'Muerte a 1 Persona'),
        ('MUERTE_2_MAS', 'Muerte a 2 o más Personas'),
    ]

    SUBTIPO_DP_CHOICES = [
        ('PERDIDA_PARCIAL_DANOS', 'Pérdida Parcial Daños'),
        ('PERDIDA_PARCIAL_HURTO', 'Pérdida Parcial Hurto'),
        ('PERDIDA_TOTAL_DANOS', 'Pérdida Total Daños'),
        ('PERDIDA_TOTAL_HURTO', 'Pérdida Total Hurto'),
    ]

    ESTADO_SINIESTRO_CHOICES = [
        ('NUEVO', 'Nuevo'),
        ('EN_PROCESO', 'En Proceso'),
        ('PENDIENTE_DOCUMENTOS', 'Pendiente de Documentos'),
        ('CERRADO_A_FAVOR', 'Cerrado a Favor del Cliente'),
        ('CERRADO_EN_CONTRA', 'Cerrado en Contra del Cliente'),
    ]

    # --- Campos del Modelo ---
    poliza = models.ForeignKey(Poliza, on_delete=models.CASCADE, related_name='siniestros')
    numero_siniestro = models.CharField("Número de Siniestro y Compañía", max_length=100)
    fecha_siniestro = models.DateField()

    tipo_siniestro = models.CharField(max_length=30, choices=TIPO_SINIESTRO_CHOICES)
    # Haremos los subtipos opcionales para flexibilidad
    subtipo_rc = models.CharField("Subtipo (Resp. Civil)", max_length=30, choices=SUBTIPO_RC_CHOICES, blank=True, null=True)
    subtipo_dp = models.CharField("Subtipo (Daños Propios)", max_length=30, choices=SUBTIPO_DP_CHOICES, blank=True, null=True)

    descripcion = models.TextField("Descripción del Siniestro")
    estado = models.CharField(max_length=30, choices=ESTADO_SINIESTRO_CHOICES, default='NUEVO')

    # Campos para archivos
    # Crearemos modelos separados para manejar múltiples documentos y fotos

    class Meta:
        ordering = ['-fecha_siniestro']

    def __str__(self):
        return f"Siniestro #{self.numero_siniestro} para Póliza {self.poliza.numero_poliza}"

# Modelos para manejar múltiples archivos por siniestro
def get_upload_path(instance, filename):
    """Genera una ruta de subida única para cada archivo."""
    return f'siniestros/{instance.siniestro.id}/documentos/{filename}'

class DocumentoSiniestro(models.Model):
    siniestro = models.ForeignKey(Siniestro, on_delete=models.CASCADE, related_name='documentos')
    documento = models.FileField(upload_to=get_upload_path)
    descripcion = models.CharField(max_length=255, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.documento.name

class FotoSiniestro(models.Model):
    siniestro = models.ForeignKey(Siniestro, on_delete=models.CASCADE, related_name='fotos')
    foto = models.ImageField(upload_to=get_upload_path)
    descripcion = models.CharField(max_length=255, blank=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.foto.name
