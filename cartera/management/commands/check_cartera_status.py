from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from polizas.models import Poliza
from cartera.models import Cuota


class Command(BaseCommand):
    help = 'Revisa y actualiza el estado de cartera de las pólizas de pago mensual.'

    def handle(self, *args, **kwargs):
        hoy = timezone.now().date()
        self.stdout.write(f"--- Iniciando revisión completa de cartera al {hoy} ---")

        polizas_a_revisar = Poliza.objects.filter(modo_pago='MENSUAL', estado='ACTIVA')

        if not polizas_a_revisar.exists():
            self.stdout.write(self.style.SUCCESS("No hay pólizas de pago mensual activas para revisar."))
            return

        contadores = {'EN_MORA': 0, 'AL_DIA': 0, 'PAGO_COMPLETO': 0}

        for poliza in polizas_a_revisar:
            with transaction.atomic():
                cuotas_actualizadas = Cuota.objects.filter(
                    poliza=poliza,
                    estado='PENDIENTE',
                    fecha_vencimiento__lt=hoy,
                ).update(estado='EN_MORA')

                if cuotas_actualizadas > 0:
                    self.stdout.write(self.style.WARNING(
                        f"  -> Póliza #{poliza.numero_poliza}: {cuotas_actualizadas} cuota(s) marcada(s) como EN MORA."
                    ))

                cuotas = poliza.cuotas.all()
                if cuotas.filter(estado='EN_MORA').exists():
                    nuevo = 'EN_MORA'
                elif cuotas.exists() and not cuotas.exclude(estado='PAGADA').exists():
                    nuevo = 'PAGO_COMPLETO'
                else:
                    nuevo = 'AL_DIA'

                if poliza.estado_cartera != nuevo:
                    poliza.estado_cartera = nuevo
                    poliza.save(update_fields=['estado_cartera'])
                    contadores[nuevo] += 1

        self.stdout.write(self.style.SUCCESS(
            f"Revisión completada. En Mora: {contadores['EN_MORA']}. "
            f"Al día: {contadores['AL_DIA']}. Pago Completo: {contadores['PAGO_COMPLETO']}."
        ))