# usuarios/views.py

from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from datetime import date, timedelta
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from polizas.models import Vehiculo
from siniestros.models import Siniestro

class PerfilClienteView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'usuarios/perfil.html'
    context_object_name = 'cliente'

    def get_object(self, queryset=None):
        """Asegura que el usuario solo pueda ver su propio perfil."""
        return self.request.user

    def get_context_data(self, **kwargs):
        """
        Prepara todos los datos necesarios para el dashboard del cliente:
        métricas, listas de pólizas, vehículos y siniestros.
        """
        context = super().get_context_data(**kwargs)
        cliente = self.object

        # --- Métricas de Pólizas ---
        polizas_cliente = cliente.polizas.all()
        
        context['polizas_activas_count'] = polizas_cliente.filter(
            estado='ACTIVA'
        ).count()

        fecha_limite = date.today() + timedelta(days=60)
        context['polizas_por_vencer_count'] = polizas_cliente.filter(
            estado='ACTIVA',
            fecha_fin__lte=fecha_limite,
            fecha_fin__gte=date.today()
        ).count()
        
        
        # --- Listas de Objetos para las Pestañas ---

        # 1. Obtenemos la lista de vehículos del cliente
        context['lista_vehiculos'] = Vehiculo.objects.filter(cliente=cliente)

        # 2. Obtenemos la lista de siniestros asociados a las pólizas del cliente
        context['lista_siniestros'] = Siniestro.objects.filter(poliza__cliente=cliente).order_by('-fecha_siniestro')
        
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
