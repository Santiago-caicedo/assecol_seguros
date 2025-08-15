# usuarios/views.py

from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from datetime import date, timedelta
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

class PerfilClienteView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'usuarios/perfil.html' # Usaremos la misma plantilla
    context_object_name = 'cliente'

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        """Añadimos las estadísticas al contexto."""
        context = super().get_context_data(**kwargs)

        polizas_cliente = self.object.polizas.all()

        # --- LÍNEA CORREGIDA ---
        # Métrica 1: Total de Pólizas Activas
        # Cambiamos 'esta_activa=True' por 'estado="ACTIVA"'
        context['polizas_activas_count'] = polizas_cliente.filter(
            estado='ACTIVA'
        ).count()

        # --- LÍNEA CORREGIDA ---
        # Métrica 2: Pólizas que vencen pronto (en los próximos 60 días)
        # Cambiamos 'esta_activa=True' por 'estado="ACTIVA"'
        fecha_limite = date.today() + timedelta(days=60)
        context['polizas_por_vencer_count'] = polizas_cliente.filter(
            estado='ACTIVA',
            fecha_fin__lte=fecha_limite,
            fecha_fin__gte=date.today() # También es buena idea asegurar que no contamos las ya vencidas
        ).count()

        return context


@login_required
def login_redirect_view(request):
    """
    Redirige a los usuarios a su dashboard correspondiente después de iniciar sesión.
    """
    if request.user.is_staff:
        # Si el usuario es administrador, lo envía al dashboard de admin.
        return redirect('dashboard_admin:dashboard_home')
    else:
        # Si es un cliente normal, lo envía a su perfil.
        return redirect('perfil')
