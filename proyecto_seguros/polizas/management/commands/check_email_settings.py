# polizas/management/commands/check_email_settings.py

from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Muestra los settings de email que Django está leyendo.'

    def handle(self, *args, **kwargs):
        self.stdout.write("--- Verificando la configuración de Email ---")

        email_settings = {
            'EMAIL_BACKEND': getattr(settings, 'EMAIL_BACKEND', 'No definido'),
            'EMAIL_HOST': getattr(settings, 'EMAIL_HOST', 'No definido'),
            'EMAIL_PORT': getattr(settings, 'EMAIL_PORT', 'No definido'),
            'EMAIL_HOST_USER': getattr(settings, 'EMAIL_HOST_USER', 'No definido'),
            'EMAIL_USE_TLS': getattr(settings, 'EMAIL_USE_TLS', 'No definido'),
            'EMAIL_USE_SSL': getattr(settings, 'EMAIL_USE_SSL', 'No definido'),
            'DEFAULT_FROM_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL', 'No definido'),
        }

        for key, value in email_settings.items():
            self.stdout.write(f"{key}: {value}")

        self.stdout.write("\n--- Verificación completa ---")
        if not email_settings.get('EMAIL_HOST') or email_settings.get('EMAIL_HOST') == 'No definido':
            self.stdout.write(self.style.ERROR("¡ERROR CRÍTICO! El EMAIL_HOST no está definido. Revisa tu archivo .env y settings.py."))