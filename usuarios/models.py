# usuarios/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class PerfilCliente(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Usuario")
    cedula = models.CharField('Cédula/ID', max_length=20, unique=True, blank=True, null=True)
    telefono = models.CharField('Teléfono', max_length=20, blank=True, null=True)
    direccion = models.CharField('Dirección', max_length=255, blank=True)

    class Meta:
        verbose_name = 'Perfil de Cliente'
        verbose_name_plural = 'Perfiles de Clientes'

    def __str__(self):
        return self.usuario.get_full_name() or self.usuario.username

# usuarios/models.py

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    """
    Crea un perfil de cliente usando get_or_create para evitar errores
    si el perfil ya fue creado por otro proceso (como el admin).
    """
    if created:
        PerfilCliente.objects.get_or_create(usuario=instance)
