# usuarios/urls.py

from django.urls import path
from .views import PerfilClienteView, login_redirect_view

urlpatterns = [
    path('perfil/', PerfilClienteView.as_view(), name='perfil'),
     path('redirect/', login_redirect_view, name='login_redirect')
]