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
    Si una póliza es NUEVA y de Contado/Crédito, crea el registro de Pago por el valor de la COMISIÓN.
    Si se ACTUALIZA, recalcula el monto del Pago si la prima (y por tanto la comisión) cambió.
    """
    if instance.modo_pago in ['CONTADO', 'CREDITO']:
        # Se calcula el valor de la comisión actual de la póliza
        comision_actual = instance.valor_comision

        if created:
            # --- Lógica de Creación ---
            if comision_actual and comision_actual > 0:
                Pago.objects.create(
                    poliza=instance,
                    fecha_pago=instance.fecha_inicio,
                    monto_pagado=comision_actual,  # <-- CORRECCIÓN: Usamos la comisión
                    estado_comision='PENDIENTE',
                    notas='Registro de comisión generado automáticamente al crear la póliza.'
                )
                print(f"--- Registro de Pago/Comisión CREADO para Póliza #{instance.numero_poliza} por valor de {comision_actual} ---")
        else:
            # --- Lógica de Actualización (Preservada y Corregida) ---
            try:
                # Buscamos el registro de Pago único asociado a esta póliza
                pago_existente = Pago.objects.get(poliza=instance, cuota__isnull=True)

                # Comparamos si el valor de la comisión guardado es diferente al nuevo
                if pago_existente.monto_pagado != comision_actual:
                    pago_existente.monto_pagado = comision_actual # <-- CORRECCIÓN: Actualizamos con la nueva comisión
                    pago_existente.save()
                    print(f"--- Registro de Pago/Comisión ACTUALIZADO para Póliza #{instance.numero_poliza} a nuevo valor de {comision_actual} ---")

            except Pago.DoesNotExist:
                # Si se edita una póliza antigua que no tuvo pago automático, lo creamos ahora
                if comision_actual and comision_actual > 0:
                     Pago.objects.create(
                        poliza=instance,
                        fecha_pago=instance.fecha_inicio,
                        monto_pagado=comision_actual, # <-- CORRECCIÓN: Usamos la comisión
                        estado_comision='PENDIENTE',
                        notas='Registro de comisión generado al actualizar póliza.'
                    )
            except Exception as e:
                print(f"Error al actualizar el pago para la póliza #{instance.numero_poliza}: {e}")