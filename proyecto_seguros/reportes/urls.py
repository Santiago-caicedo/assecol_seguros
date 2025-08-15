from django.urls import path
from .views import panel_reportes_view

app_name = 'reportes'

urlpatterns = [
    path('', panel_reportes_view, name='panel_reportes'),
]