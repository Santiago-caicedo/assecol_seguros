# polizas/tests.py
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from .models import TipoSeguro, CompaniaAseguradora, Poliza, Vehiculo, Asesor
from cartera.models import Cuota, Pago


class TipoSeguroModelTest(TestCase):
    """Tests para el modelo TipoSeguro."""

    def test_crear_tipo_seguro(self):
        """Verifica que se puede crear un tipo de seguro correctamente."""
        tipo = TipoSeguro.objects.create(
            nombre='SOAT',
            descripcion='Seguro obligatorio',
            comision_porcentaje=Decimal('10.00'),
            porcentaje_iva=Decimal('19.00')
        )
        self.assertEqual(tipo.nombre, 'SOAT')
        self.assertEqual(tipo.comision_porcentaje, Decimal('10.00'))
        self.assertEqual(tipo.porcentaje_iva, Decimal('19.00'))

    def test_str_representation(self):
        """Verifica la representación string del tipo de seguro."""
        tipo = TipoSeguro.objects.create(nombre='Seguro de Vida')
        self.assertEqual(str(tipo), 'Seguro de Vida')


class PolizaModelTest(TestCase):
    """Tests para el modelo Poliza y sus cálculos financieros."""

    @classmethod
    def setUpTestData(cls):
        """Configura los datos de prueba una vez para toda la clase."""
        cls.cliente = User.objects.create_user(
            username='cliente_test',
            email='cliente@test.com',
            password='testpass123',
            first_name='Juan',
            last_name='Pérez'
        )

        cls.tipo_seguro = TipoSeguro.objects.create(
            nombre='Todo Riesgo',
            descripcion='Póliza de vehículo todo riesgo',
            comision_porcentaje=Decimal('15.00'),
            porcentaje_iva=Decimal('19.00')
        )

        cls.compania = CompaniaAseguradora.objects.create(
            nombre='Seguros Test S.A.'
        )

        cls.asesor = Asesor.objects.create(
            nombre_completo='María González'
        )

    def crear_poliza(self, **kwargs):
        """Helper para crear pólizas de prueba."""
        defaults = {
            'cliente': self.cliente,
            'tipo_seguro': self.tipo_seguro,
            'compania_aseguradora': self.compania,
            'numero_poliza': f'POL-{Poliza.objects.count() + 1:04d}',
            'fecha_inicio': date.today(),
            'fecha_fin': date.today() + timedelta(days=365),
            'valor_prima_sin_iva': Decimal('1000000.00'),
            'modo_pago': 'CONTADO',
            'estado': 'ACTIVA',
        }
        defaults.update(kwargs)
        return Poliza.objects.create(**defaults)

    # ==================== Tests de valor_iva ====================

    def test_valor_iva_calculo_correcto(self):
        """Verifica que el IVA se calcula correctamente."""
        poliza = self.crear_poliza(valor_prima_sin_iva=Decimal('1000000.00'))
        # 1,000,000 * 19% = 190,000
        expected_iva = Decimal('190000.00')
        self.assertEqual(poliza.valor_iva, expected_iva)

    def test_valor_iva_con_prima_cero(self):
        """Verifica el IVA cuando la prima es cero."""
        poliza = self.crear_poliza(valor_prima_sin_iva=Decimal('0.00'))
        self.assertEqual(poliza.valor_iva, Decimal('0'))

    def test_valor_iva_con_diferentes_porcentajes(self):
        """Verifica el IVA con diferentes porcentajes de IVA."""
        tipo_sin_iva = TipoSeguro.objects.create(
            nombre='Seguro Sin IVA',
            porcentaje_iva=Decimal('0.00'),
            comision_porcentaje=Decimal('10.00')
        )
        poliza = self.crear_poliza(
            tipo_seguro=tipo_sin_iva,
            valor_prima_sin_iva=Decimal('500000.00'),
            numero_poliza='POL-SIN-IVA'
        )
        self.assertEqual(poliza.valor_iva, Decimal('0'))

    # ==================== Tests de valor_total_a_pagar ====================

    def test_valor_total_a_pagar_calculo_correcto(self):
        """Verifica que el total a pagar es prima + IVA."""
        poliza = self.crear_poliza(valor_prima_sin_iva=Decimal('1000000.00'))
        # 1,000,000 + 190,000 = 1,190,000
        expected_total = Decimal('1190000.00')
        self.assertEqual(poliza.valor_total_a_pagar, expected_total)

    def test_valor_total_a_pagar_sin_iva(self):
        """Verifica el total cuando no hay IVA."""
        tipo_sin_iva = TipoSeguro.objects.create(
            nombre='Exento IVA',
            porcentaje_iva=Decimal('0.00'),
            comision_porcentaje=Decimal('10.00')
        )
        poliza = self.crear_poliza(
            tipo_seguro=tipo_sin_iva,
            valor_prima_sin_iva=Decimal('500000.00'),
            numero_poliza='POL-EXENTO'
        )
        self.assertEqual(poliza.valor_total_a_pagar, Decimal('500000.00'))

    # ==================== Tests de valor_comision ====================

    def test_valor_comision_calculo_correcto(self):
        """Verifica que la comisión se calcula correctamente."""
        poliza = self.crear_poliza(valor_prima_sin_iva=Decimal('1000000.00'))
        # 1,000,000 * 15% = 150,000
        expected_comision = Decimal('150000.00')
        self.assertEqual(poliza.valor_comision, expected_comision)

    def test_valor_comision_con_prima_cero(self):
        """Verifica la comisión cuando la prima es cero."""
        poliza = self.crear_poliza(valor_prima_sin_iva=Decimal('0.00'))
        self.assertEqual(poliza.valor_comision, Decimal('0'))

    def test_valor_comision_diferentes_porcentajes(self):
        """Verifica la comisión con diferentes porcentajes."""
        tipo_alta_comision = TipoSeguro.objects.create(
            nombre='Alta Comisión',
            comision_porcentaje=Decimal('25.00'),
            porcentaje_iva=Decimal('19.00')
        )
        poliza = self.crear_poliza(
            tipo_seguro=tipo_alta_comision,
            valor_prima_sin_iva=Decimal('2000000.00'),
            numero_poliza='POL-ALTA-COM'
        )
        # 2,000,000 * 25% = 500,000
        self.assertEqual(poliza.valor_comision, Decimal('500000.00'))

    # ==================== Tests de calcular_prorrateo_cancelacion ====================

    def test_prorrateo_solo_aplica_contado(self):
        """Verifica que el prorrateo solo aplica para pólizas de contado."""
        poliza = self.crear_poliza(modo_pago='MENSUAL')
        poliza.fecha_cancelacion = date.today() + timedelta(days=30)
        devolucion, comision = poliza.calcular_prorrateo_cancelacion()
        self.assertIsNone(devolucion)
        self.assertIsNone(comision)

    def test_prorrateo_requiere_fecha_cancelacion(self):
        """Verifica que se requiere fecha de cancelación."""
        poliza = self.crear_poliza(modo_pago='CONTADO')
        poliza.fecha_cancelacion = None
        devolucion, comision = poliza.calcular_prorrateo_cancelacion()
        self.assertIsNone(devolucion)
        self.assertIsNone(comision)

    def test_prorrateo_calculo_mitad_periodo(self):
        """Verifica el prorrateo cuando se cancela a mitad del periodo."""
        fecha_inicio = date(2024, 1, 1)
        fecha_fin = date(2025, 1, 1)  # 366 días (2024 es bisiesto)

        poliza = self.crear_poliza(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            valor_prima_sin_iva=Decimal('1000000.00'),
            modo_pago='CONTADO',
            numero_poliza='POL-PRORRATEO-1'
        )

        # Cancelar a los 183 días (mitad del periodo aproximadamente)
        poliza.fecha_cancelacion = fecha_inicio + timedelta(days=183)
        devolucion, comision_devuelta = poliza.calcular_prorrateo_cancelacion()

        # Días totales: 366
        # Días activos: 183
        # Prima consumida: 1,000,000 * (183/366) = 500,000 aprox
        # Devolución: 1,000,000 - 500,000 = 500,000 aprox

        self.assertIsNotNone(devolucion)
        self.assertIsNotNone(comision_devuelta)
        self.assertGreater(devolucion, 0)
        self.assertGreater(comision_devuelta, 0)

    def test_prorrateo_cancelacion_inmediata(self):
        """Verifica el prorrateo cuando se cancela el mismo día."""
        fecha_inicio = date(2024, 1, 1)
        fecha_fin = date(2025, 1, 1)

        poliza = self.crear_poliza(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            valor_prima_sin_iva=Decimal('1000000.00'),
            modo_pago='CONTADO',
            numero_poliza='POL-PRORRATEO-2'
        )

        poliza.fecha_cancelacion = fecha_inicio  # Cancelación el mismo día
        devolucion, comision_devuelta = poliza.calcular_prorrateo_cancelacion()

        # Si se cancela el mismo día, debería devolver casi todo
        self.assertIsNotNone(devolucion)
        self.assertAlmostEqual(float(devolucion), 1000000.0, delta=5000)

    def test_prorrateo_ultimo_dia(self):
        """Verifica el prorrateo cuando se cancela el último día."""
        fecha_inicio = date(2024, 1, 1)
        fecha_fin = date(2025, 1, 1)

        poliza = self.crear_poliza(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            valor_prima_sin_iva=Decimal('1000000.00'),
            modo_pago='CONTADO',
            numero_poliza='POL-PRORRATEO-3'
        )

        poliza.fecha_cancelacion = fecha_fin - timedelta(days=1)
        devolucion, comision_devuelta = poliza.calcular_prorrateo_cancelacion()

        # Casi toda la prima fue consumida
        self.assertIsNotNone(devolucion)
        self.assertLess(float(devolucion), 10000)  # Muy poco por devolver

    # ==================== Tests de Estados ====================

    def test_estado_inicial_activa(self):
        """Verifica que las pólizas se crean en estado ACTIVA."""
        poliza = self.crear_poliza()
        self.assertEqual(poliza.estado, 'ACTIVA')

    def test_estado_cartera_inicial_al_dia(self):
        """Verifica que el estado de cartera inicial es AL_DIA."""
        poliza = self.crear_poliza()
        self.assertEqual(poliza.estado_cartera, 'AL_DIA')


class PolizaSignalsTest(TestCase):
    """Tests para los signals de Poliza."""

    @classmethod
    def setUpTestData(cls):
        cls.cliente = User.objects.create_user(
            username='cliente_signals',
            email='signals@test.com',
            password='testpass123'
        )

        cls.tipo_seguro = TipoSeguro.objects.create(
            nombre='Seguro Test',
            comision_porcentaje=Decimal('10.00'),
            porcentaje_iva=Decimal('19.00')
        )

        cls.compania = CompaniaAseguradora.objects.create(
            nombre='Compañía Test'
        )

    def test_signal_crear_cuotas_mensual(self):
        """Verifica que se crean cuotas automáticamente para pago mensual."""
        poliza = Poliza.objects.create(
            cliente=self.cliente,
            tipo_seguro=self.tipo_seguro,
            compania_aseguradora=self.compania,
            numero_poliza='POL-MENSUAL-001',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=365),
            valor_prima_sin_iva=Decimal('1200000.00'),
            modo_pago='MENSUAL',
            plazo_meses=12
        )

        cuotas = Cuota.objects.filter(poliza=poliza)
        self.assertEqual(cuotas.count(), 12)

        # Verificar monto de cada cuota
        monto_esperado = Decimal('1200000.00') / 12
        for cuota in cuotas:
            self.assertEqual(cuota.monto_cuota, monto_esperado)

    def test_signal_crear_pago_contado(self):
        """Verifica que se crea un Pago automáticamente para póliza de contado."""
        poliza = Poliza.objects.create(
            cliente=self.cliente,
            tipo_seguro=self.tipo_seguro,
            compania_aseguradora=self.compania,
            numero_poliza='POL-CONTADO-001',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=365),
            valor_prima_sin_iva=Decimal('1000000.00'),
            modo_pago='CONTADO'
        )

        pagos = Pago.objects.filter(poliza=poliza)
        self.assertEqual(pagos.count(), 1)

        pago = pagos.first()
        comision_esperada = Decimal('1000000.00') * Decimal('0.10')
        self.assertEqual(pago.monto_pagado, comision_esperada)
        self.assertEqual(pago.estado_comision, 'PENDIENTE')

    def test_signal_no_crear_cuotas_contado(self):
        """Verifica que NO se crean cuotas para pólizas de contado."""
        poliza = Poliza.objects.create(
            cliente=self.cliente,
            tipo_seguro=self.tipo_seguro,
            compania_aseguradora=self.compania,
            numero_poliza='POL-CONTADO-002',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=365),
            valor_prima_sin_iva=Decimal('500000.00'),
            modo_pago='CONTADO'
        )

        cuotas = Cuota.objects.filter(poliza=poliza)
        self.assertEqual(cuotas.count(), 0)


class VehiculoModelTest(TestCase):
    """Tests para el modelo Vehiculo."""

    @classmethod
    def setUpTestData(cls):
        cls.cliente = User.objects.create_user(
            username='cliente_vehiculo',
            email='vehiculo@test.com',
            password='testpass123'
        )

    def test_crear_vehiculo(self):
        """Verifica que se puede crear un vehículo correctamente."""
        vehiculo = Vehiculo.objects.create(
            cliente=self.cliente,
            placa='ABC123',
            marca='Toyota',
            modelo='Corolla',
            ano=2022
        )
        self.assertEqual(vehiculo.placa, 'ABC123')
        self.assertEqual(vehiculo.cliente, self.cliente)

    def test_str_representation(self):
        """Verifica la representación string del vehículo."""
        vehiculo = Vehiculo.objects.create(
            cliente=self.cliente,
            placa='XYZ789',
            marca='Honda',
            modelo='Civic'
        )
        self.assertIn('XYZ789', str(vehiculo))
        self.assertIn('Honda', str(vehiculo))

    def test_placa_unica(self):
        """Verifica que la placa debe ser única."""
        Vehiculo.objects.create(
            cliente=self.cliente,
            placa='UNI001'
        )
        with self.assertRaises(Exception):
            Vehiculo.objects.create(
                cliente=self.cliente,
                placa='UNI001'
            )


class AsesorModelTest(TestCase):
    """Tests para el modelo Asesor."""

    def test_crear_asesor(self):
        """Verifica que se puede crear un asesor correctamente."""
        asesor = Asesor.objects.create(nombre_completo='Carlos Rodríguez')
        self.assertEqual(asesor.nombre_completo, 'Carlos Rodríguez')

    def test_str_representation(self):
        """Verifica la representación string del asesor."""
        asesor = Asesor.objects.create(nombre_completo='Ana López')
        self.assertEqual(str(asesor), 'Ana López')
