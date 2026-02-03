# polizas/management/commands/seed_data.py

from django.core.management.base import BaseCommand
from polizas.models import TipoSeguro, CompaniaAseguradora
from siniestros.models import TipoSiniestro, SubtipoSiniestro

class Command(BaseCommand):
    help = 'Carga los datos iniciales de configuración en la base de datos.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("--- Iniciando carga de datos iniciales... ---"))

        # --- Creando Compañías Aseguradoras ---
        companias = ['Sura', 'Allianz', 'Seguros Bolívar', 'Mapfre', 'Axa Colpatria']
        for nombre in companias:
            obj, created = CompaniaAseguradora.objects.get_or_create(nombre=nombre)
            if created: self.stdout.write(f"Creada Compañía: {obj.nombre}")

        # --- Creando Tipos de Seguro ---
        tipos_seguro = [
            {'nombre': 'SOAT', 'comision': 8.0, 'iva': 0.0},
            {'nombre': 'Póliza Todo Riesgo Vehículo', 'comision': 15.0, 'iva': 19.0},
            {'nombre': 'Seguro de Vida', 'comision': 20.0, 'iva': 0.0},
            {'nombre': 'Seguro Hogar', 'comision': 18.0, 'iva': 19.0},
        ]
        for tipo in tipos_seguro:
            obj, created = TipoSeguro.objects.get_or_create(
                nombre=tipo['nombre'], 
                defaults={'comision_porcentaje': tipo['comision'], 'porcentaje_iva': tipo['iva']}
            )
            if created: self.stdout.write(f"Creado Tipo de Seguro: {obj.nombre}")

        # --- Creando Tipos y Subtipos de Siniestro ---
        tipo_rc, _ = TipoSiniestro.objects.get_or_create(nombre='Responsabilidad Civil Extracontractual')
        tipo_dp, _ = TipoSiniestro.objects.get_or_create(nombre='Daños Propios')

        subtipos_rc = ['Solo Daños', 'Daños y Lesiones a 1 Persona', 'Lesiones a 1 Persona', 'Lesiones a 2 o más Personas', 'Daños y Muerte a 1 Persona', 'Daños y Muerte a 2 o más Personas', 'Muerte a 1 Persona', 'Muerte a 2 o más Personas']
        for nombre in subtipos_rc:
            SubtipoSiniestro.objects.get_or_create(nombre=nombre, tipo=tipo_rc)

        subtipos_dp = ['Pérdida Parcial Daños', 'Pérdida Parcial Hurto', 'Pérdida Total Daños', 'Pérdida Total Hurto']
        for nombre in subtipos_dp:
            SubtipoSiniestro.objects.get_or_create(nombre=nombre, tipo=tipo_dp)

        self.stdout.write(self.style.SUCCESS("Tipos y subtipos de siniestro creados/verificados."))
        self.stdout.write(self.style.SUCCESS("--- Carga de datos iniciales completada. ---"))