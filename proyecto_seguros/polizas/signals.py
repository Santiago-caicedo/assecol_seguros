# polizas/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Poliza
from cartera.models import Cuota, Pago
from dateutil.relativedelta import relativedelta

@receiver(post_save, sender=Poliza)
def crear_plan_de_pagos(sender, instance, created, **kwargs):
    """
    Si una póliza es NUEVA y su modo de pago es MENSUAL,
    crea automáticamente las cuotas correspondientes.
    """
    # Solo se ejecuta al crear una póliza nueva
    if created and instance.modo_pago == 'MENSUAL':

        # 👇 CAMBIO CLAVE AQUÍ 👇
        # Usamos 'valor_prima_sin_iva' en lugar de 'prima_total'
        monto_cuota = instance.valor_prima_sin_iva / instance.plazo_meses

        # Creamos una cuota por cada mes del plazo
        for i in range(instance.plazo_meses):
            fecha_vencimiento = instance.fecha_inicio + relativedelta(months=i + 1)

            Cuota.objects.create(
                poliza=instance,
                numero_cuota=i + 1,
                fecha_vencimiento=fecha_vencimiento,
                monto_cuota=monto_cuota
            )



@receiver(post_save, sender=Poliza)
def actualizar_recordatorio_soat(sender, instance, **kwargs):
    """
    Si se guarda una póliza de tipo SOAT que está vinculada a un vehículo,
    actualiza la fecha del recordatorio en el modelo Vehiculo.
    """
    # Verificamos si la póliza tiene un tipo de seguro y un vehículo asignado
    if instance.tipo_seguro and instance.vehiculo:
        # Comparamos el nombre en minúsculas para ser flexibles (SOAT, Soat, soat)
        if 'soat' in instance.tipo_seguro.nombre.lower():
            vehiculo = instance.vehiculo
            # Actualizamos el recordatorio con la fecha de fin de la póliza
            vehiculo.soat_vencimiento_recordatorio = instance.fecha_fin
            vehiculo.save()
            print(f"--- Recordatorio de SOAT actualizado para el vehículo {vehiculo.placa} a la fecha {instance.fecha_fin} ---")



@receiver(post_save, sender=Poliza)
def crear_pago_para_contado_y_credito(sender, instance, created, **kwargs):
    """
    Si una póliza es NUEVA y de Contado/Crédito, crea el registro de Pago.
    Si se ACTUALIZA y sigue ACTIVA, recalcula el monto del Pago si la prima cambió.
    """
    if instance.modo_pago in ['CONTADO', 'CREDITO']:
        comision_actual = instance.valor_comision

        if created:
            # --- Lógica de Creación (sin cambios) ---
            if comision_actual and comision_actual > 0:
                Pago.objects.create(
                    poliza=instance,
                    fecha_pago=instance.fecha_inicio,
                    monto_pagado=comision_actual,
                    estado_comision='PENDIENTE',
                    notas='Registro de comisión generado automáticamente al crear la póliza.'
                )
        else:
            # --- Lógica de Actualización MEJORADA ---
            # 👇 AÑADIMOS ESTA CONDICIÓN CRÍTICA 👇
            if instance.estado == 'ACTIVA':
                try:
                    pago_existente = Pago.objects.get(poliza=instance, cuota__isnull=True)
                    if pago_existente.monto_pagado != comision_actual:
                        pago_existente.monto_pagado = comision_actual
                        pago_existente.save()
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
                except Exception as e:
                    print(f"Error al actualizar el pago para la póliza #{instance.numero_poliza}: {e}")