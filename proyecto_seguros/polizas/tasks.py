from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Poliza
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

@shared_task
def enviar_recordatorios_vencimiento():
    """
    Tarea de Celery que se ejecuta periódicamente para encontrar pólizas
    próximas a vencer y enviar notificaciones por correo electrónico
    tanto al cliente como a un correo administrativo.
    """
    print("--- Ejecutando tarea: enviar_recordatorios_vencimiento ---")
    hoy = timezone.now().date()
    # Define el rango de búsqueda para pólizas que vencen en los próximos 30 días
    fecha_limite = hoy + timedelta(days=30)

    # Busca las pólizas que cumplen con los criterios.
    # Usamos select_related para optimizar la consulta y evitar múltiples accesos a la BD.
    polizas_por_vencer = Poliza.objects.filter(
        estado='ACTIVA',
        fecha_fin__gte=hoy,
        fecha_fin__lte=fecha_limite
    ).select_related('cliente', 'tipo_seguro', 'vehiculo')

    if not polizas_por_vencer.exists():
        print("No se encontraron pólizas por vencer en los próximos 30 días.")
        return "No hay pólizas por vencer para procesar."

    print(f"Se encontraron {polizas_por_vencer.count()} pólizas por vencer. Enviando correos...")
    
    for poliza in polizas_por_vencer:
        # Preparamos un contexto único con el objeto poliza completo para pasarlo a las plantillas
        contexto_email = {
            'poliza': poliza,
        }
        
        # --- Preparación del Correo para el Cliente ---
        cuerpo_html_cliente = render_to_string('emails/recordatorio_vencimiento.html', contexto_email)
        asunto_cliente = f"Recordatorio: Tu póliza #{poliza.numero_poliza} está por vencer"
        
        email_cliente = EmailMessage(
            asunto_cliente,
            cuerpo_html_cliente,
            settings.DEFAULT_FROM_EMAIL,
            [poliza.cliente.email]
        )
        email_cliente.content_subtype = "html"  # Especificamos que el contenido es HTML

        # --- Preparación del Correo para el Administrador ---
        cuerpo_html_admin = render_to_string('emails/recordatorio_vencimiento_admin.html', contexto_email)
        asunto_admin = f"Alerta Vencimiento: Póliza de {poliza.cliente.get_full_name()}"
        
        email_admin = EmailMessage(
            asunto_admin,
            cuerpo_html_admin,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL]
        )
        email_admin.content_subtype = "html"

        # --- Envío de Correos ---
        try:
            email_cliente.send()
            print(f"Correo enviado exitosamente a CLIENTE: {poliza.cliente.email} para la póliza #{poliza.numero_poliza}")
            
            if settings.ADMIN_EMAIL:
                email_admin.send()
                print(f"Copia enviada exitosamente a ADMIN: {settings.ADMIN_EMAIL}")

        except Exception as e:
            print(f"ERROR al enviar correos para póliza #{poliza.numero_poliza}: {e}")
    
    return f"Proceso completado. Se procesaron {polizas_por_vencer.count()} pólizas."