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
    # 👇 1. AÑADE ESTA LÍNEA DE DEPURACIÓN 👇
    print(f"--- Señal post_save ejecutada para Póliza #{instance.numero_poliza} ---")

    if created:
        # 👇 2. AÑADE ESTA LÍNEA DE DEPURACIÓN 👇
        print(f"   -> La póliza es NUEVA (created=True). Modo de pago: {instance.modo_pago}")

        if instance.modo_pago == 'MENSUAL':
            # 👇 3. AÑADE ESTA LÍNEA DE DEPURACIÓN 👇
            print(f"   --> ¡CONDICIÓN CUMPLIDA! Creando plan de pagos de {instance.plazo_meses} cuotas...")

            monto_cuota = instance.prima_total / instance.plazo_meses
            for i in range(instance.plazo_meses):
                fecha_vencimiento = instance.fecha_inicio + relativedelta(months=i + 1)
                Cuota.objects.create(
                    poliza=instance,
                    numero_cuota=i + 1,
                    fecha_vencimiento=fecha_vencimiento,
                    monto_cuota=monto_cuota
                )
            print("   --> Plan de pagos creado exitosamente.")
    else:
        print("   -> La póliza es una ACTUALIZACIÓN (created=False). No se hace nada.")



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
    Si una póliza es NUEVA y su modo de pago es CONTADO o CREDITO,
    crea un registro de Pago por el valor de la PRIMA SIN IVA.
    """
    if created and instance.modo_pago in ['CONTADO', 'CREDITO']:
        if instance.valor_prima_sin_iva and instance.valor_prima_sin_iva > 0:
            Pago.objects.create(
                poliza=instance,
                fecha_pago=instance.fecha_inicio,
                # 👇 LA LÍNEA MÁS IMPORTANTE Y CORREGIDA 👇
                # Guardamos la prima sin IVA como base para futuros cálculos.
                monto_pagado=instance.valor_prima_sin_iva,
                estado_comision='PENDIENTE',
                notas='Registro de pago (base de comisión) generado automáticamente.'
            )