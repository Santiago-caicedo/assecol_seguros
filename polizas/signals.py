# polizas/signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Poliza
from cartera.models import Cuota, Pago
from dateutil.relativedelta import relativedelta

logger = logging.getLogger('polizas')


@receiver(post_save, sender=Poliza)
def crear_plan_de_pagos(sender, instance, created, **kwargs):
    """
    Si una póliza es NUEVA y su modo de pago es MENSUAL,
    crea automáticamente las cuotas correspondientes.
    """
    if created and instance.modo_pago == 'MENSUAL':
        try:
            monto_cuota = instance.valor_prima_sin_iva / instance.plazo_meses
            cuotas_a_crear = []

            for i in range(instance.plazo_meses):
                fecha_vencimiento = instance.fecha_inicio + relativedelta(months=i + 1)
                cuotas_a_crear.append(
                    Cuota(
                        poliza=instance,
                        numero_cuota=i + 1,
                        fecha_vencimiento=fecha_vencimiento,
                        monto_cuota=monto_cuota
                    )
                )

            # Bulk create para mejor performance
            Cuota.objects.bulk_create(cuotas_a_crear)
            logger.info(
                f"Plan de pagos creado para póliza #{instance.numero_poliza}: "
                f"{instance.plazo_meses} cuotas de ${monto_cuota:.2f}"
            )
        except Exception as e:
            logger.exception(
                f"Error al crear plan de pagos para póliza #{instance.numero_poliza}: {e}"
            )
            raise  # Re-lanzamos para que la transacción falle si es necesario


@receiver(post_save, sender=Poliza)
def actualizar_recordatorio_soat(sender, instance, **kwargs):
    """
    Si se guarda una póliza de tipo SOAT que está vinculada a un vehículo,
    actualiza la fecha del recordatorio en el modelo Vehiculo.
    """
    if instance.tipo_seguro and instance.vehiculo:
        if 'soat' in instance.tipo_seguro.nombre.lower():
            try:
                vehiculo = instance.vehiculo
                vehiculo.soat_vencimiento_recordatorio = instance.fecha_fin
                vehiculo.save()
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
    if instance.modo_pago in ['CONTADO', 'CREDITO']:
        comision_actual = instance.valor_comision

        if created:
            # Lógica de Creación
            if comision_actual and comision_actual > 0:
                try:
                    Pago.objects.create(
                        poliza=instance,
                        fecha_pago=instance.fecha_inicio,
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
            if instance.estado == 'ACTIVA':
                try:
                    pago_existente = Pago.objects.get(poliza=instance, cuota__isnull=True)
                    if pago_existente.monto_pagado != comision_actual:
                        monto_anterior = pago_existente.monto_pagado
                        pago_existente.monto_pagado = comision_actual
                        pago_existente.save()
                        logger.info(
                            f"Pago actualizado para póliza #{instance.numero_poliza}: "
                            f"${monto_anterior:.2f} -> ${comision_actual:.2f}"
                        )
                except Pago.DoesNotExist:
                    # Si no existe, lo creamos (caso borde)
                    if comision_actual and comision_actual > 0:
                        Pago.objects.create(
                            poliza=instance,
                            fecha_pago=instance.fecha_inicio,
                            monto_pagado=comision_actual,
                            estado_comision='PENDIENTE',
                            notas='Registro de comisión generado al actualizar póliza.'
                        )
                        logger.warning(
                            f"Pago faltante creado para póliza #{instance.numero_poliza} "
                            f"durante actualización: ${comision_actual:.2f}"
                        )
                except Exception as e:
                    logger.exception(
                        f"Error al actualizar pago para póliza #{instance.numero_poliza}: {e}"
                    )
                    # No re-lanzamos aquí para no interrumpir la actualización de la póliza
