# polizas/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Poliza
from cartera.models import Cuota, Pago
from dateutil.relativedelta import relativedelta

logger = logging.getLogger('polizas')


def _generar_cuotas_mensuales(poliza):
    """Genera el plan de cuotas para una póliza MENSUAL. Asume no hay cuotas previas."""
    if not poliza.plazo_meses or poliza.plazo_meses <= 0:
        logger.warning(
            f"No se generan cuotas para póliza #{poliza.numero_poliza}: plazo_meses inválido."
        )
        return
    monto_cuota = poliza.valor_prima_sin_iva / poliza.plazo_meses
    cuotas_a_crear = [
        Cuota(
            poliza=poliza,
            numero_cuota=i + 1,
            fecha_vencimiento=poliza.fecha_inicio + relativedelta(months=i + 1),
            monto_cuota=monto_cuota,
        )
        for i in range(poliza.plazo_meses)
    ]
    Cuota.objects.bulk_create(cuotas_a_crear)
    logger.info(
        f"Plan de pagos creado para póliza #{poliza.numero_poliza}: "
        f"{poliza.plazo_meses} cuotas de ${monto_cuota:.2f}"
    )


@receiver(post_save, sender=Poliza)
def crear_plan_de_pagos(sender, instance, created, **kwargs):
    """Crea cuotas mensuales al crear póliza MENSUAL si aún no existen."""
    if instance.modo_pago != 'MENSUAL':
        return
    if instance.cuotas.exists():
        return
    try:
        _generar_cuotas_mensuales(instance)
    except Exception as e:
        logger.exception(
            f"Error al crear plan de pagos para póliza #{instance.numero_poliza}: {e}"
        )
        if created:
            raise


@receiver(post_save, sender=Poliza)
def actualizar_recordatorio_soat(sender, instance, created, **kwargs):
    """
    Si se guarda una póliza de tipo SOAT vinculada a un vehículo, actualiza el
    recordatorio de vencimiento en el Vehículo — solo si la fecha de fin de la
    póliza es posterior al recordatorio existente, para no pisar fechas más
    recientes con renovaciones anteriores.
    """
    if not (instance.tipo_seguro and instance.vehiculo):
        return
    if 'soat' not in instance.tipo_seguro.nombre.lower():
        return
    if instance.estado != 'ACTIVA':
        return
    try:
        vehiculo = instance.vehiculo
        actual = vehiculo.soat_vencimiento_recordatorio
        if actual and actual >= instance.fecha_fin:
            return
        vehiculo.soat_vencimiento_recordatorio = instance.fecha_fin
        vehiculo.save(update_fields=['soat_vencimiento_recordatorio'])
        logger.info(
            f"Recordatorio SOAT actualizado para vehículo {vehiculo.placa} "
            f"a la fecha {instance.fecha_fin}"
        )
    except Exception as e:
        logger.exception(
            f"Error al actualizar recordatorio SOAT para vehículo "
            f"{instance.vehiculo.placa}: {e}"
        )


@receiver(post_save, sender=Poliza)
def crear_pago_para_contado_y_credito(sender, instance, created, **kwargs):
    """
    Si una póliza es NUEVA y de Contado/Crédito, crea el registro de Pago.
    Si se ACTUALIZA y sigue ACTIVA, recalcula el monto del Pago si la prima cambió.
    """
    if instance.modo_pago in ['CONTADO', 'CREDITO', 'FINANCIADO']:
        comision_actual = instance.valor_comision

        if created:
            # Lógica de Creación
            if comision_actual and comision_actual > 0:
                try:
                    fecha_pago = instance.fecha_pago_contado if instance.modo_pago == 'CONTADO' and instance.fecha_pago_contado else instance.fecha_inicio
                    Pago.objects.create(
                        poliza=instance,
                        fecha_pago=fecha_pago,
                        monto_pagado=comision_actual,
                        estado_comision='PENDIENTE',
                        notas='Registro de comisión generado automáticamente al crear la póliza.'
                    )
                    logger.info(
                        f"Pago de comisión creado para póliza #{instance.numero_poliza}: "
                        f"${comision_actual:.2f}"
                    )
                except Exception as e:
                    logger.exception(
                        f"Error al crear pago para póliza #{instance.numero_poliza}: {e}"
                    )
                    raise
        else:
            # Lógica de Actualización
            if instance.estado != 'ACTIVA':
                return
            try:
                pagos = Pago.objects.filter(poliza=instance, cuota__isnull=True)
                pago_existente = pagos.first()
                if pagos.count() > 1:
                    logger.warning(
                        f"Póliza #{instance.numero_poliza} tiene {pagos.count()} pagos sin cuota; "
                        f"solo se actualiza el primero."
                    )
                if pago_existente is None:
                    if comision_actual and comision_actual > 0:
                        Pago.objects.create(
                            poliza=instance,
                            fecha_pago=instance.fecha_pago_contado or instance.fecha_inicio,
                            monto_pagado=comision_actual,
                            estado_comision='PENDIENTE',
                            notas='Registro de comisión generado al actualizar póliza.'
                        )
                        logger.warning(
                            f"Pago faltante creado para póliza #{instance.numero_poliza} "
                            f"durante actualización: ${comision_actual:.2f}"
                        )
                elif pago_existente.estado_comision == 'LIQUIDADA':
                    logger.warning(
                        f"Pago de póliza #{instance.numero_poliza} ya está LIQUIDADO; "
                        f"no se ajusta monto aunque la prima cambió."
                    )
                elif pago_existente.monto_pagado != comision_actual:
                    monto_anterior = pago_existente.monto_pagado
                    pago_existente.monto_pagado = comision_actual
                    pago_existente.save(update_fields=['monto_pagado'])
                    logger.info(
                        f"Pago actualizado para póliza #{instance.numero_poliza}: "
                        f"${monto_anterior:.2f} -> ${comision_actual:.2f}"
                    )
            except Exception as e:
                logger.exception(
                    f"Error al actualizar pago para póliza #{instance.numero_poliza}: {e}"
                )
