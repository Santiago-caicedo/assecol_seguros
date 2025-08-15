# dashboard_admin/views.py

from django.shortcuts import render
from django.views.generic import ListView,  CreateView, UpdateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_POST
from polizas.models import Poliza, TipoSeguro, CompaniaAseguradora, Vehiculo
from polizas.forms import PolicyForm
from .forms import CancelPolicyForm, VehiculoForm
from .forms import ClientCreationForm, ClientUpdateForm, TipoSeguroForm, CompaniaAseguradoraForm
from datetime import date, timedelta
from django.utils import timezone
from django.db.models import Sum, Q
import json
from django.db.models.functions import TruncMonth
from django.db.models import Count
from cartera.models import Cuota, Pago




def es_admin(user):
    """Función para verificar si un usuario es staff."""
    return user.is_staff


@login_required
@user_passes_test(es_admin)
def dashboard_home_view(request):
    # --- Métricas existentes ---
    # Métrica 1: Total de Clientes (excluyendo staff)
    total_clientes = User.objects.filter(is_staff=False).count()

    # --- LÍNEA CORREGIDA ---
    # Métrica 2: Total de Pólizas Activas
    # Cambiamos 'esta_activa=True' por 'estado="ACTIVA"'
    total_polizas_activas = Poliza.objects.filter(estado='ACTIVA').count()

    # --- LÍNEAS CORREGIDAS ---
    # Métrica 3: Pólizas que vencen pronto (en los próximos 30 días)
    fecha_limite = date.today() + timedelta(days=30)
    polizas_por_vencer = Poliza.objects.filter(
        estado='ACTIVA', # Cambiamos 'esta_activa=True'
        fecha_fin__lte=fecha_limite,
        fecha_fin__gte=date.today()
    ).count()

    # --- Datos para Gráfico 1: Pólizas por Tipo ---
    # Agrupamos por tipo de seguro y contamos cuántas pólizas tiene cada uno
    polizas_por_tipo = TipoSeguro.objects.annotate(cantidad=Count('polizas')).order_by('-cantidad')

    # Preparamos las etiquetas y los datos para Chart.js
    labels_pie_chart = [tipo.nombre for tipo in polizas_por_tipo]
    data_pie_chart = [tipo.cantidad for tipo in polizas_por_tipo]

    # --- Datos para Gráfico 2: Nuevos Clientes por Mes (últimos 12 meses) ---
    hace_un_ano = date.today() - timedelta(days=365)
    clientes_por_mes = User.objects.filter(date_joined__gte=hace_un_ano, is_staff=False) \
        .annotate(month=TruncMonth('date_joined')) \
        .values('month') \
        .annotate(count=Count('id')) \
        .order_by('month')

    labels_bar_chart = [mes['month'].strftime('%b %Y') for mes in clientes_por_mes]
    data_bar_chart = [mes['count'] for mes in clientes_por_mes]

    context = {
        'total_clientes': total_clientes,
        'total_polizas_activas': total_polizas_activas,
        'polizas_por_vencer': polizas_por_vencer,
        # Pasamos los datos del gráfico a la plantilla, convertidos a JSON
        'labels_pie_chart': json.dumps(labels_pie_chart),
        'data_pie_chart': json.dumps(data_pie_chart),
        'labels_bar_chart': json.dumps(labels_bar_chart),
        'data_bar_chart': json.dumps(data_bar_chart),
    }
    return render(request, 'dashboard_admin/dashboard_home.html', context)



class ClientListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'dashboard_admin/client_list.html'
    context_object_name = 'clientes'

    def test_func(self):
        """
        Esta función de prueba asegura que solo los usuarios que son 'staff'
        puedan acceder a esta vista.
        """
        return self.request.user.is_staff

    def get_queryset(self):
        """
        Sobrescribimos el queryset para excluir a otros administradores
        de la lista de "clientes".
        """
        return User.objects.filter(is_staff=False).order_by('first_name', 'last_name')


class ClientCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = User
    form_class = ClientCreationForm
    template_name = 'dashboard_admin/client_form.html'
    success_url = reverse_lazy('dashboard_admin:lista_clientes') # A dónde ir tras crear el cliente

    def test_func(self):
        """Misma prueba de seguridad: solo para administradores."""
        return self.request.user.is_staff
    

class ClientUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = ClientUpdateForm
    template_name = 'dashboard_admin/client_form.html'
    success_url = reverse_lazy('dashboard_admin:lista_clientes')

    def test_func(self):
        """Misma prueba de seguridad: solo para administradores."""
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        """Añadimos un título al contexto para reutilizar la plantilla."""
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Cliente'
        return context




class ClientPolicyListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Poliza
    template_name = 'dashboard_admin/client_policy_list.html'
    context_object_name = 'polizas'

    def test_func(self):
        """Misma prueba de seguridad: solo para administradores."""
        return self.request.user.is_staff

    def get_queryset(self):
        """
        Filtra las pólizas para mostrar solo las del cliente
        cuya PK viene en la URL.
        """
        # Obtenemos el usuario (cliente) basado en la 'pk' de la URL
        self.cliente = User.objects.get(pk=self.kwargs['pk'])
        # Devolvemos solo las pólizas de ese cliente
        return Poliza.objects.filter(cliente=self.cliente)

    def get_context_data(self, **kwargs):
        """
        Añadimos el objeto del cliente al contexto para poder
        mostrar su nombre en el título de la plantilla.
        """
        context = super().get_context_data(**kwargs)
        context['cliente'] = self.cliente
        return context



class PolicyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Poliza
    form_class = PolicyForm
    template_name = 'dashboard_admin/policy_form.html'

    def test_func(self):
        """Misma prueba de seguridad: solo para administradores."""
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        """Añade el cliente al contexto para mostrar su nombre."""
        context = super().get_context_data(**kwargs)
        # Obtenemos el cliente de la URL para mostrarlo en la plantilla
        self.cliente = User.objects.get(pk=self.kwargs['pk'])
        context['cliente'] = self.cliente
        return context

    def form_valid(self, form):
        """
        Asigna el cliente a la póliza antes de guardarla.
        """
        # Obtenemos el cliente de la URL de nuevo
        cliente = User.objects.get(pk=self.kwargs['pk'])
        # Asignamos la instancia del cliente al campo 'cliente' de la póliza
        form.instance.cliente = cliente
        return super().form_valid(form)

    def get_success_url(self):
        """Redirige a la lista de pólizas del cliente tras el éxito."""
        return reverse_lazy('dashboard_admin:lista_polizas_cliente', kwargs={'pk': self.kwargs['pk']})
    
    def form_invalid(self, form):
        """
        Este método se ejecuta cuando form.is_valid() devuelve False.
        Lo usamos para imprimir los errores en la consola.
        """
        print("--- ERRORES DEL FORMULARIO DE PÓLIZA ---")
        print(form.errors.as_json())
        print("---------------------------------------")
        return super().form_invalid(form)
    

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        cliente = User.objects.get(pk=self.kwargs['pk'])
        # Filtramos el campo 'vehiculo' para mostrar solo los de este cliente
        form.fields['vehiculo'].queryset = Vehiculo.objects.filter(cliente=cliente)
        return form


class PolicyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Poliza
    form_class = PolicyForm
    template_name = 'dashboard_admin/policy_form.html'
    context_object_name = 'poliza'

    def test_func(self):
        """Misma prueba de seguridad: solo para administradores."""
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        """
        Añadimos un título y el cliente al contexto para que la plantilla
        sepa que estamos editando.
        """
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Póliza'
        # El objeto self.object es la póliza que se está editando
        context['cliente'] = self.object.cliente
        return context

    def get_success_url(self):
        """
        Redirige a la lista de pólizas del cliente al que pertenece
        la póliza que acabamos de editar.
        """
        # El objeto self.object es la póliza que se acaba de guardar
        cliente_pk = self.object.cliente.pk
        return reverse_lazy('dashboard_admin:lista_polizas_cliente', kwargs={'pk': cliente_pk})
    

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # En UpdateView, el cliente se obtiene de la póliza misma
        cliente = self.object.cliente
        form.fields['vehiculo'].queryset = Vehiculo.objects.filter(cliente=cliente)
        return form
    



class TipoSeguroListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = TipoSeguro
    template_name = 'dashboard_admin/tiposeguro_list.html'
    context_object_name = 'tipos_de_seguro'

    def test_func(self):
        return self.request.user.is_staff

class TipoSeguroCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = TipoSeguro
    form_class = TipoSeguroForm
    template_name = 'dashboard_admin/tiposeguro_form.html'
    success_url = reverse_lazy('dashboard_admin:lista_tipos_seguro')

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Añadir Nuevo Tipo de Seguro'
        return context



class CompaniaAseguradoraListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = CompaniaAseguradora
    template_name = 'dashboard_admin/compania_list.html'
    context_object_name = 'companias'

    def test_func(self):
        return self.request.user.is_staff

class CompaniaAseguradoraCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = CompaniaAseguradora
    form_class = CompaniaAseguradoraForm
    template_name = 'dashboard_admin/compania_form.html'
    success_url = reverse_lazy('dashboard_admin:lista_companias')

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Añadir Nueva Compañía Aseguradora'
        return context  

class CompaniaAseguradoraUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CompaniaAseguradora
    form_class = CompaniaAseguradoraForm
    template_name = 'dashboard_admin/compania_form.html'
    success_url = reverse_lazy('dashboard_admin:lista_companias')

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Compañía Aseguradora'
        return context

class CompaniaAseguradoraDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = CompaniaAseguradora
    template_name = 'dashboard_admin/confirm_delete.html' # Reutilizamos la plantilla
    success_url = reverse_lazy('dashboard_admin:lista_companias')

    def test_func(self):
        return self.request.user.is_staff

class TipoSeguroUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = TipoSeguro
    form_class = TipoSeguroForm
    template_name = 'dashboard_admin/tiposeguro_form.html'
    success_url = reverse_lazy('dashboard_admin:lista_tipos_seguro')

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Tipo de Seguro'
        return context

class TipoSeguroDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = TipoSeguro
    template_name = 'dashboard_admin/confirm_delete.html' # Plantilla genérica de confirmación
    success_url = reverse_lazy('dashboard_admin:lista_tipos_seguro')

    def test_func(self):
        return self.request.user.is_staff


#Vista para cancelar póliza
class PolicyCancelView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Poliza
    form_class = CancelPolicyForm
    template_name = 'dashboard_admin/policy_confirm_cancel.html'
    context_object_name = 'poliza'

    def test_func(self):
        return self.request.user.is_staff
    


    def get_context_data(self, **kwargs):
        """
        Calcula los valores del prorrateo para mostrarlos en la confirmación.
        """
        context = super().get_context_data(**kwargs)
        poliza = self.object # La póliza que estamos cancelando

        if poliza.modo_pago == 'CONTADO':
            # Hacemos un "simulacro" de la cancelación para obtener los valores
            poliza.fecha_cancelacion = timezone.now().date()
            devolucion, comision_devuelta = poliza.calcular_prorrateo_cancelacion()

            # Pasamos los valores calculados a la plantilla
            context['devolucion_calculada'] = devolucion
            context['comision_devuelta_calculada'] = comision_devuelta

        return context
    

    def form_valid(self, form):
        poliza = form.save(commit=False)
        poliza.estado = 'CANCELADA'
        poliza.fecha_cancelacion = timezone.now().date()

        # 👇 LÓGICA DE PRORRATEO AÑADIDA 👇
        # Si la póliza es de contado, calculamos y guardamos la devolución
        if poliza.modo_pago == 'CONTADO':
            devolucion, comision_devuelta = poliza.calcular_prorrateo_cancelacion()
            if devolucion is not None:
                poliza.monto_devolucion = devolucion
                poliza.comision_devuelta = comision_devuelta

        poliza.save()
        # El form.save() original ahora se llama desde el super()
        return super().form_valid(form)

    def get_success_url(self):
        cliente_pk = self.object.cliente.pk
        return reverse_lazy('dashboard_admin:lista_polizas_cliente', kwargs={'pk': cliente_pk})


#CARTERA 

class CarteraGeneralView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Poliza
    template_name = 'dashboard_admin/cartera_general.html'
    context_object_name = 'polizas'
    paginate_by = 25

    def test_func(self):
        return self.request.user.is_staff

    def get_queryset(self):
        # Primero, obtenemos el queryset base de las pólizas
        queryset = Poliza.objects.select_related('cliente', 'tipo_seguro').all()
        
        # Luego, aplicamos el filtro si se seleccionó un cliente
        cliente_id = self.request.GET.get('cliente')
        if cliente_id:
            # Filtramos las pólizas por el ID del cliente
            queryset = queryset.filter(cliente_id=cliente_id)
        
        return queryset

    def get_context_data(self, **kwargs):
        # Obtenemos el contexto base de la ListView
        context = super().get_context_data(**kwargs)
        
        # Obtenemos el queryset de pólizas (ya filtrado si aplica)
        queryset_filtrado = context['polizas']

        # Calculamos las métricas basadas en las pólizas filtradas
        total_ventas = queryset_filtrado.aggregate(total=Sum('prima_total'))['total'] or 0
        total_comisiones = sum(p.valor_comision for p in queryset_filtrado if p.valor_comision is not None)

        # Obtenemos las pólizas en mora (esto siempre es sobre todas las pólizas, no solo las filtradas)
        polizas_en_mora = Poliza.objects.filter(estado_cartera='EN_MORA')

        # --- ESTA ES LA PARTE IMPORTANTE ---
        # Pasamos la lista COMPLETA de clientes para el menú desplegable
        context['todos_los_clientes'] = User.objects.filter(is_staff=False).order_by('first_name')
        
        # Añadimos las métricas y datos adicionales al contexto
        context['total_ventas'] = total_ventas
        context['total_comisiones'] = total_comisiones
        context['polizas_en_mora'] = polizas_en_mora
        context['cliente_seleccionado'] = self.request.GET.get('cliente')
        
        return context




class PolicyPortfolioDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Poliza
    template_name = 'dashboard_admin/policy_portfolio_detail.html'
    context_object_name = 'poliza'

    def test_func(self):
        return self.request.user.is_staff
    

    def get_context_data(self, **kwargs):
        """
        Añade explícitamente la lista de cuotas al contexto para asegurar
        que la plantilla las reciba.
        """
        context = super().get_context_data(**kwargs)
        # self.object es la póliza que la DetailView ya ha recuperado
        context['lista_de_cuotas'] = self.object.cuotas.all()
        return context



@login_required
@user_passes_test(es_admin)
@require_POST # Asegura que esta vista solo acepte peticiones POST
def marcar_cuota_pagada_view(request, pk):
    cuota = get_object_or_404(Cuota, pk=pk)
    poliza = cuota.poliza

    # Cambiamos el estado de la cuota
    cuota.estado = 'PAGADA'
    cuota.save()

    # Creamos un registro de Pago asociado a esta cuota
    Pago.objects.create(
        poliza=cuota.poliza,
        cuota=cuota,
        fecha_pago=timezone.now().date(),
        monto_pagado=cuota.monto_cuota,
        notas=f"Pago registrado automáticamente para la cuota #{cuota.numero_cuota}."
    )


    otras_cuotas_en_mora = poliza.cuotas.filter(estado='EN_MORA').exists()

    if not otras_cuotas_en_mora:
        # Si ya no hay cuotas en mora, la póliza vuelve a estar al día
        poliza.estado_cartera = 'AL_DIA'
        poliza.save()

    # Redirigimos de vuelta a la página de detalle de cartera de la póliza
    return redirect('dashboard_admin:detalle_cartera_poliza', pk=cuota.poliza.pk)


@login_required
@user_passes_test(es_admin)
@require_POST
def marcar_cuota_mora_view(request, pk):
    cuota = get_object_or_404(Cuota, pk=pk)

    # Cambiamos el estado de la cuota
    cuota.estado = 'EN_MORA'
    cuota.save()

    # Redirigimos de vuelta a la misma página
    return redirect('dashboard_admin:detalle_cartera_poliza', pk=cuota.poliza.pk)


class VehiculoListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Vehiculo
    template_name = 'dashboard_admin/vehiculo_list.html'
    context_object_name = 'vehiculos'

    def test_func(self):
        return self.request.user.is_staff

class VehiculoCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Vehiculo
    form_class = VehiculoForm
    template_name = 'dashboard_admin/vehiculo_form.html'
    success_url = reverse_lazy('dashboard_admin:lista_vehiculos')

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Añadir Nuevo Vehículo'
        return context


class VehiculoUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Vehiculo
    form_class = VehiculoForm # Reutilizamos el mismo formulario de creación
    template_name = 'dashboard_admin/vehiculo_form.html'
    success_url = reverse_lazy('dashboard_admin:lista_vehiculos')

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Editar Vehículo'
        return context

class VehiculoDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Vehiculo
    template_name = 'dashboard_admin/confirm_delete.html' # Reutilizamos la plantilla genérica
    success_url = reverse_lazy('dashboard_admin:lista_vehiculos')

    def test_func(self):
        return self.request.user.is_staff