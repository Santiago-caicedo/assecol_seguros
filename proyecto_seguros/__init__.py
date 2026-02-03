# proyecto_seguros/__init__.py

# Esto importa la app de Celery cuando Django se inicia
from .celery import app as celery_app

__all__ = ('celery_app',)