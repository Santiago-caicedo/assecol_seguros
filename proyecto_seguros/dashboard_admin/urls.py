# dashboard_admin/urls.py
from django.urls import path
from .views import (
    CarteraGeneralView,
    ClientListView, 
    ClientCreateView, 
    ClientUpdateView, 
    ClientPolicyListView,
    CompaniaAseguradoraCreateView,
    CompaniaAseguradoraDeleteView,
    CompaniaAseguradoraListView,
    CompaniaAseguradoraUpdateView,
    PolicyCancelView,
    PolicyCreateView,
    PolicyPortfolioDetailView,
    PolicyUpdateView,
    TipoSeguroCreateView,
    TipoSeguroDeleteView,
    TipoSeguroListView,
    TipoSeguroUpdateView,
    VehiculoCreateView,
    VehiculoDeleteView,
    VehiculoListView,
    VehiculoUpdateView, 
    dashboard_home_view,
    marcar_cuota_mora_view,
    marcar_cuota_pagada_view,
    test_select2_view
)

app_name = 'dashboard_admin'

urlpatterns = [
    # La raíz del dashboard ahora es la vista de estadísticas
    path('', dashboard_home_view, name='dashboard_home'),

    # Las otras vistas ahora cuelgan de esta raíz
    path('clientes/', ClientListView.as_view(), name='lista_clientes'),
    path('clientes/nuevo/', ClientCreateView.as_view(), name='crear_cliente'),
    path('clientes/editar/<int:pk>/', ClientUpdateView.as_view(), name='editar_cliente'),
    path('clientes/<int:pk>/polizas/', ClientPolicyListView.as_view(), name='lista_polizas_cliente'),
    path('clientes/<int:pk>/polizas/nueva/', PolicyCreateView.as_view(), name='crear_poliza_cliente'),
    path('polizas/editar/<int:pk>/', PolicyUpdateView.as_view(), name='editar_poliza'),
    path('tipos-de-seguro/', TipoSeguroListView.as_view(), name='lista_tipos_seguro'),
    path('tipos-de-seguro/nuevo/', TipoSeguroCreateView.as_view(), name='crear_tipo_seguro'),
    path('companias/', CompaniaAseguradoraListView.as_view(), name='lista_companias'),
    path('companias/nueva/', CompaniaAseguradoraCreateView.as_view(), name='crear_compania'),
    path('tipos-de-seguro/editar/<int:pk>/', TipoSeguroUpdateView.as_view(), name='editar_tipo_seguro'),
    path('tipos-de-seguro/eliminar/<int:pk>/', TipoSeguroDeleteView.as_view(), name='eliminar_tipo_seguro'),
    path('companias/editar/<int:pk>/', CompaniaAseguradoraUpdateView.as_view(), name='editar_compania'),
    path('companias/eliminar/<int:pk>/', CompaniaAseguradoraDeleteView.as_view(), name='eliminar_compania'),
    path('polizas/cancelar/<int:pk>/', PolicyCancelView.as_view(), name='cancelar_poliza'),
    path('cartera/', CarteraGeneralView.as_view(), name='cartera_general'),
    path('polizas/<int:pk>/cartera/', PolicyPortfolioDetailView.as_view(), name='detalle_cartera_poliza'),
    path('cuotas/<int:pk>/marcar-pagada/', marcar_cuota_pagada_view, name='marcar_cuota_pagada'),
    path('cuotas/<int:pk>/marcar-mora/', marcar_cuota_mora_view, name='marcar_cuota_mora'),
    path('vehiculos/', VehiculoListView.as_view(), name='lista_vehiculos'),
    path('vehiculos/nuevo/', VehiculoCreateView.as_view(), name='crear_vehiculo'),
    path('vehiculos/editar/<int:pk>/', VehiculoUpdateView.as_view(), name='editar_vehiculo'),
    path('vehiculos/eliminar/<int:pk>/', VehiculoDeleteView.as_view(), name='eliminar_vehiculo'),
    
    path('test-select2/', test_select2_view, name='test_select2'),

]