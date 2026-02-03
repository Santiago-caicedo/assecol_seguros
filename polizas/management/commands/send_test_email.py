# polizas/management/commands/send_test_email.py

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Envía un correo electrónico de prueba para verificar la configuración SMTP.'

    def add_arguments(self, parser):
        parser.add_argument('email_receptor', type=str, help='La dirección de correo electrónico a la que se enviará la prueba.')

    def handle(self, *args, **kwargs):
        email_receptor = kwargs['email_receptor']

        self.stdout.write(f"Intentando enviar un correo de prueba a: {email_receptor}...")

        try:
            send_mail(
                subject='Correo de Prueba - CRM Assecol Seguros',
                message='Si recibes este correo, ¡la configuración SMTP de tu aplicación Django funciona correctamente!',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email_receptor],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS('¡Correo de prueba enviado exitosamente! Revisa tu bandeja de entrada.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error al enviar el correo: {e}'))
            self.stdout.write(self.style.WARNING('Verifica tus credenciales en el archivo .env y la configuración en settings.py.'))