# polizas/apps.py
from django.apps import AppConfig

class PolizasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'polizas'

    def ready(self):
        # Importa las señales cuando la aplicación esté lista
        import polizas.signals
