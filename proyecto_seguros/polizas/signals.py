# polizas/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Poliza
from cartera.models import Cuota
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