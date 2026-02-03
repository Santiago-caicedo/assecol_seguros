from django.core.management.base import BaseCommand
from django.utils import timezone
from polizas.models import Poliza
from cartera.models import Cuota
from django.db.models import Q

class Command(BaseCommand):
    help = 'Revisa y actualiza el estado de cartera de todas las pólizas de pago mensual.'

    def handle(self, *args, **kwargs):
        hoy = timezone.now().date()
        self.stdout.write(f"--- Iniciando revisión completa de cartera al {hoy} ---")

        polizas_a_revisar = Poliza.objects.filter(
            modo_pago='MENSUAL',
            estado='ACTIVA'
        )

        if not polizas_a_revisar.exists():
            self.stdout.write(self.style.SUCCESS("No hay pólizas de pago mensual activas para revisar."))
            return

        polizas_actualizadas_a_mora = 0
        polizas_actualizadas_al_dia = 0

        for poliza in polizas_a_revisar:
            # 1. Primero, actualizamos todas las cuotas PENDIENTES que ya se vencieron a EN_MORA.
            cuotas_actualizadas = Cuota.objects.filter(
                poliza=poliza,
                estado='PENDIENTE',
                fecha_vencimiento__lt=hoy
            ).update(estado='EN_MORA')

            if cuotas_actualizadas > 0:
                self.stdout.write(self.style.WARNING(
                    f"  -> Póliza #{poliza.numero_poliza}: {cuotas_actualizadas} cuota(s) marcada(s) como EN MORA."
                ))

            # 2. Ahora, revisamos si la póliza tiene ALGUNA cuota en mora.
            tiene_cuotas_en_mora = poliza.cuotas.filter(estado='EN_MORA').exists()

            if tiene_cuotas_en_mora:
                # Si hay al menos una cuota en mora, la póliza completa está en mora.
                if poliza.estado_cartera != 'EN_MORA':
                    poliza.estado_cartera = 'EN_MORA'
                    poliza.save()
                    polizas_actualizadas_a_mora += 1
            else:
                # Si no hay ninguna cuota en mora, la póliza está al día.
                if poliza.estado_cartera != 'AL_DIA':
                    poliza.estado_cartera = 'AL_DIA'
                    poliza.save()
                    polizas_actualizadas_al_dia += 1

        self.stdout.write(self.style.SUCCESS(
            f"Revisión completada. Pólizas actualizadas a 'En Mora': {polizas_actualizadas_a_mora}. "
            f"Pólizas actualizadas a 'Al día': {polizas_actualizadas_al_dia}."
        ))