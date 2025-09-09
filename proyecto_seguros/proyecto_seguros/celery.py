# proyecto_seguros/celery.py
import os
from celery import Celery

# Establece el módulo de settings de Django para el programa 'celery'.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proyecto_seguros.settings')

app = Celery('proyecto_seguros')

# Lee la configuración de Celery desde los settings de Django (CELERY_...)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descubre automáticamente las tareas en los archivos tasks.py de cada app
app.autodiscover_tasks()



# --- CONFIGURACIÓN DE CELERY BEAT (PROGRAMADOR DE TAREAS) ---
CELERY_BEAT_SCHEDULE = {
    'enviar-recordatorios-diarios': {
        'task': 'polizas.tasks.enviar_recordatorios_vencimiento', # La ruta a nuestra tarea
        'schedule': 86400.0,  # Se ejecuta cada 24 horas (en segundos)
        # También puedes usar crontab para más control, ej: 'schedule': crontab(hour=7, minute=30),
    },
}