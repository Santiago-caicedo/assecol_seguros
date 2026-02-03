import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Poliza
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger('polizas')


@shared_task
def enviar_recordatorios_vencimiento():
    """
    Tarea de Celery que se ejecuta periódicamente para encontrar pólizas
    próximas a vencer y enviar notificaciones por correo electrónico
    tanto al cliente como a un correo administrativo.
    """
    logger.info("Iniciando tarea: enviar_recordatorios_vencimiento")

    hoy = timezone.now().date()
    fecha_limite = hoy + timedelta(days=30)

    polizas_por_vencer = Poliza.objects.filter(
        estado='ACTIVA',
        fecha_fin__gte=hoy,
        fecha_fin__lte=fecha_limite
    ).select_related('cliente', 'tipo_seguro', 'vehiculo')

    if not polizas_por_vencer.exists():
        logger.info("No se encontraron pólizas por vencer en los próximos 30 días.")
        return "No hay pólizas por vencer para procesar."

    total_polizas = polizas_por_vencer.count()
    logger.info(f"Se encontraron {total_polizas} pólizas por vencer. Enviando correos...")

    enviados_exitosos = 0
    errores = 0

    for poliza in polizas_por_vencer:
        contexto_email = {'poliza': poliza}

        try:
            # Correo para el Cliente
            cuerpo_html_cliente = render_to_string('emails/recordatorio_vencimiento.html', contexto_email)
            asunto_cliente = f"Recordatorio: Tu póliza #{poliza.numero_poliza} está por vencer"

            email_cliente = EmailMessage(
                asunto_cliente,
                cuerpo_html_cliente,
                settings.DEFAULT_FROM_EMAIL,
                [poliza.cliente.email]
            )
            email_cliente.content_subtype = "html"
            email_cliente.send()

            logger.info(
                f"Correo de recordatorio enviado a cliente {poliza.cliente.email} "
                f"para póliza #{poliza.numero_poliza}"
            )

            # Correo para el Administrador
            if settings.ADMIN_EMAIL:
                cuerpo_html_admin = render_to_string('emails/recordatorio_vencimiento_admin.html', contexto_email)
                asunto_admin = f"Alerta Vencimiento: Póliza de {poliza.cliente.get_full_name()}"

                email_admin = EmailMessage(
                    asunto_admin,
                    cuerpo_html_admin,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL]
                )
                email_admin.content_subtype = "html"
                email_admin.send()

                logger.debug(f"Copia de recordatorio enviada a admin: {settings.ADMIN_EMAIL}")

            enviados_exitosos += 1

        except Exception as e:
            errores += 1
            logger.exception(
                f"Error al enviar correos para póliza #{poliza.numero_poliza} "
                f"(cliente: {poliza.cliente.email}): {e}"
            )
            # Continuamos con las siguientes pólizas en lugar de detener todo el proceso

    resultado = (
        f"Proceso completado. Total: {total_polizas}, "
        f"Enviados: {enviados_exitosos}, Errores: {errores}"
    )

    if errores > 0:
        logger.warning(resultado)
    else:
        logger.info(resultado)

    return resultado
