# siniestros/models.py
from django.db import models
from polizas.models import Poliza

# --- MODELOS NUEVOS Y REESTRUCTURADOS ---

class TipoSiniestro(models.Model):
    """ Las categorías principales: 'Responsabilidad Civil', 'Daños Propios' """
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class SubtipoSiniestro(models.Model):
    """ Las opciones específicas: 'Solo Daños', 'Pérdida Parcial Hurto', etc. """
    tipo = models.ForeignKey(TipoSiniestro, on_delete=models.CASCADE, related_name='subtipos')
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.tipo.nombre} - {self.nombre}"

class Siniestro(models.Model):
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
    
    # 👇 CAMBIO CLAVE: Un siniestro ahora puede tener MUCHOS subtipos afectados 👇
    subtipos_afectados = models.ManyToManyField(SubtipoSiniestro, related_name='siniestros')

    descripcion = models.TextField("Descripción del Siniestro")
    estado = models.CharField(max_length=30, choices=ESTADO_SINIESTRO_CHOICES, default='NUEVO')
    
    class Meta:
        ordering = ['-fecha_siniestro']

    def __str__(self):
        return f"Siniestro #{self.numero_siniestro} para Póliza {self.poliza.numero_poliza}"

# --- MODELOS PARA ARCHIVOS (SIN CAMBIOS) ---

def get_upload_path(instance, filename):
    """Genera una ruta de subida única para cada archivo."""
    # Aseguramos que el siniestro tenga un ID antes de construir la ruta
    siniestro_id = instance.siniestro.id if instance.siniestro and instance.siniestro.id else 'temp'
    return f'siniestros/{siniestro_id}/documentos/{filename}'

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
