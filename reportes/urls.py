from django.urls import path
from .views import panel_reportes_view, reporte_asesor_view

app_name = 'reportes'

urlpatterns = [
    path('', panel_reportes_view, name='panel_reportes'),
    path('rendimiento-asesor/', reporte_asesor_view, name='reporte_asesor'),
]