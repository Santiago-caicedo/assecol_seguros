from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import PerfilCliente

# Define un 'inline' para el PerfilCliente.
# Esto le dice a Django: "Quiero editar PerfilCliente en la misma página que el modelo User"
class PerfilClienteInline(admin.StackedInline):
    model = PerfilCliente
    can_delete = False
    verbose_name_plural = 'Perfiles de Clientes'

# Define una nueva clase de administración para User que incluye nuestro inline.
class UserAdmin(BaseUserAdmin):
    inlines = (PerfilClienteInline,)

# Vuelve a registrar el modelo User con nuestro UserAdmin personalizado.
# Primero lo "des-registramos"...
admin.site.unregister(User)
# ...y luego lo registramos con nuestra nueva configuración.
admin.site.register(User, UserAdmin)