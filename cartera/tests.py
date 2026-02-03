# cartera/tests.py
from decimal import Decimal
from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from polizas.models import TipoSeguro, CompaniaAseguradora, Poliza
from .models import Cuota, Pago


class CuotaModelTest(TestCase):
    """Tests para el modelo Cuota."""

    @classmethod
    def setUpTestData(cls):
        cls.cliente = User.objects.create_user(
            username='cliente_cuota',
            email='cuota@test.com',
            password='testpass123'
        )

        cls.tipo_seguro = TipoSeguro.objects.create(
            nombre='Seguro Cuota Test',
            comision_porcentaje=Decimal('10.00'),
            porcentaje_iva=Decimal('19.00')
        )

        cls.compania = CompaniaAseguradora.objects.create(
            nombre='Compañía Cuota Test'
        )

        # Crear póliza sin disparar signal de cuotas
        cls.poliza = Poliza.objects.create(
            cliente=cls.cliente,
            tipo_seguro=cls.tipo_seguro,
            compania_aseguradora=cls.compania,
            numero_poliza='POL-CUOTA-TEST',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=365),
            valor_prima_sin_iva=Decimal('1200000.00'),
            modo_pago='CONTADO'  # Para evitar signal de cuotas
        )

    def test_crear_cuota(self):
        """Verifica que se puede crear una cuota correctamente."""
        cuota = Cuota.objects.create(
            poliza=self.poliza,
            numero_cuota=1,
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_cuota=Decimal('100000.00')
        )
        self.assertEqual(cuota.numero_cuota, 1)
        self.assertEqual(cuota.monto_cuota, Decimal('100000.00'))
        self.assertEqual(cuota.estado, 'PENDIENTE')

    def test_str_representation(self):
        """Verifica la representación string de la cuota."""
        cuota = Cuota.objects.create(
            poliza=self.poliza,
            numero_cuota=3,
            fecha_vencimiento=date.today() + timedelta(days=90),
            monto_cuota=Decimal('100000.00')
        )
        self.assertIn('Cuota 3', str(cuota))
        self.assertIn(self.poliza.numero_poliza, str(cuota))

    def test_estado_inicial_pendiente(self):
        """Verifica que el estado inicial de una cuota es PENDIENTE."""
        cuota = Cuota.objects.create(
            poliza=self.poliza,
            numero_cuota=1,
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_cuota=Decimal('100000.00')
        )
        self.assertEqual(cuota.estado, 'PENDIENTE')

    def test_unique_together_poliza_numero_cuota(self):
        """Verifica que no puede haber dos cuotas con el mismo número para la misma póliza."""
        Cuota.objects.create(
            poliza=self.poliza,
            numero_cuota=5,
            fecha_vencimiento=date.today() + timedelta(days=150),
            monto_cuota=Decimal('100000.00')
        )

        with self.assertRaises(Exception):
            Cuota.objects.create(
                poliza=self.poliza,
                numero_cuota=5,  # Mismo número
                fecha_vencimiento=date.today() + timedelta(days=180),
                monto_cuota=Decimal('100000.00')
            )

    def test_cambiar_estado_a_pagada(self):
        """Verifica que se puede cambiar el estado a PAGADA."""
        cuota = Cuota.objects.create(
            poliza=self.poliza,
            numero_cuota=6,
            fecha_vencimiento=date.today() + timedelta(days=30),
            monto_cuota=Decimal('100000.00')
        )
        cuota.estado = 'PAGADA'
        cuota.save()

        cuota.refresh_from_db()
        self.assertEqual(cuota.estado, 'PAGADA')

    def test_cambiar_estado_a_mora(self):
        """Verifica que se puede cambiar el estado a EN_MORA."""
        cuota = Cuota.objects.create(
            poliza=self.poliza,
            numero_cuota=7,
            fecha_vencimiento=date.today() - timedelta(days=10),  # Vencida
            monto_cuota=Decimal('100000.00')
        )
        cuota.estado = 'EN_MORA'
        cuota.save()

        cuota.refresh_from_db()
        self.assertEqual(cuota.estado, 'EN_MORA')

    def test_ordering_por_numero_cuota(self):
        """Verifica que las cuotas se ordenan por número."""
        Cuota.objects.create(
            poliza=self.poliza,
            numero_cuota=12,
            fecha_vencimiento=date.today() + timedelta(days=360),
            monto_cuota=Decimal('100000.00')
        )
        Cuota.objects.create(
            poliza=self.poliza,
            numero_cuota=10,
            fecha_vencimiento=date.today() + timedelta(days=300),
            monto_cuota=Decimal('100000.00')
        )
        Cuota.objects.create(
            poliza=self.poliza,
            numero_cuota=11,
            fecha_vencimiento=date.today() + timedelta(days=330),
            monto_cuota=Decimal('100000.00')
        )

        cuotas = list(Cuota.objects.filter(poliza=self.poliza, numero_cuota__gte=10))
        numeros = [c.numero_cuota for c in cuotas]
        self.assertEqual(numeros, [10, 11, 12])


class PagoModelTest(TestCase):
    """Tests para el modelo Pago."""

    @classmethod
    def setUpTestData(cls):
        cls.cliente = User.objects.create_user(
            username='cliente_pago',
            email='pago@test.com',
            password='testpass123'
        )

        cls.tipo_seguro = TipoSeguro.objects.create(
            nombre='Seguro Pago Test',
            comision_porcentaje=Decimal('10.00'),
            porcentaje_iva=Decimal('19.00')
        )

        cls.compania = CompaniaAseguradora.objects.create(
            nombre='Compañía Pago Test'
        )

    def crear_poliza(self, numero_poliza, modo_pago='CONTADO'):
        """Helper para crear pólizas sin disparar signals problemáticos."""
        return Poliza.objects.create(
            cliente=self.cliente,
            tipo_seguro=self.tipo_seguro,
            compania_aseguradora=self.compania,
            numero_poliza=numero_poliza,
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=365),
            valor_prima_sin_iva=Decimal('1000000.00'),
            modo_pago=modo_pago
        )

    def test_crear_pago_sin_cuota(self):
        """Verifica que se puede crear un pago sin cuota asociada (contado)."""
        poliza = self.crear_poliza('POL-PAGO-001')
        # El signal ya crea un pago, verificamos que existe
        pagos = Pago.objects.filter(poliza=poliza)
        self.assertTrue(pagos.exists())

    def test_crear_pago_con_cuota(self):
        """Verifica que se puede crear un pago con cuota asociada (mensual)."""
        poliza = self.crear_poliza('POL-PAGO-002', modo_pago='MENSUAL')
        # Limpiar pagos creados por signals para crear uno manualmente
        Pago.objects.filter(poliza=poliza).delete()

        cuota = Cuota.objects.filter(poliza=poliza).first()
        pago = Pago.objects.create(
            poliza=poliza,
            cuota=cuota,
            fecha_pago=date.today(),
            monto_pagado=Decimal('10000.00'),
            estado_comision='PENDIENTE'
        )

        self.assertEqual(pago.cuota, cuota)
        self.assertEqual(pago.monto_pagado, Decimal('10000.00'))

    def test_estado_comision_inicial_pendiente(self):
        """Verifica que el estado inicial de comisión es PENDIENTE."""
        poliza = self.crear_poliza('POL-PAGO-003')
        pago = Pago.objects.filter(poliza=poliza).first()
        self.assertEqual(pago.estado_comision, 'PENDIENTE')

    def test_cambiar_estado_comision_a_liquidada(self):
        """Verifica que se puede marcar una comisión como liquidada."""
        poliza = self.crear_poliza('POL-PAGO-004')
        pago = Pago.objects.filter(poliza=poliza).first()

        pago.estado_comision = 'LIQUIDADA'
        pago.save()

        pago.refresh_from_db()
        self.assertEqual(pago.estado_comision, 'LIQUIDADA')

    def test_str_representation(self):
        """Verifica la representación string del pago."""
        poliza = self.crear_poliza('POL-PAGO-005')
        pago = Pago.objects.filter(poliza=poliza).first()

        str_pago = str(pago)
        self.assertIn('Pago', str_pago)
        self.assertIn(poliza.numero_poliza, str_pago)

    def test_pago_con_comprobante(self):
        """Verifica que se puede crear un pago con notas."""
        poliza = self.crear_poliza('POL-PAGO-006')
        pago = Pago.objects.filter(poliza=poliza).first()

        pago.notas = 'Pago recibido en efectivo'
        pago.save()

        pago.refresh_from_db()
        self.assertEqual(pago.notas, 'Pago recibido en efectivo')

    def test_ordering_por_fecha_descendente(self):
        """Verifica que los pagos se ordenan por fecha descendente."""
        poliza = self.crear_poliza('POL-PAGO-007')
        # Limpiar pagos existentes
        Pago.objects.filter(poliza=poliza).delete()

        Pago.objects.create(
            poliza=poliza,
            fecha_pago=date.today() - timedelta(days=30),
            monto_pagado=Decimal('1000.00')
        )
        Pago.objects.create(
            poliza=poliza,
            fecha_pago=date.today(),
            monto_pagado=Decimal('2000.00')
        )
        Pago.objects.create(
            poliza=poliza,
            fecha_pago=date.today() - timedelta(days=15),
            monto_pagado=Decimal('1500.00')
        )

        pagos = list(Pago.objects.filter(poliza=poliza))
        montos = [p.monto_pagado for p in pagos]
        # El más reciente primero
        self.assertEqual(montos, [Decimal('2000.00'), Decimal('1500.00'), Decimal('1000.00')])


class CuotaPagoIntegrationTest(TestCase):
    """Tests de integración entre Cuota y Pago."""

    @classmethod
    def setUpTestData(cls):
        cls.cliente = User.objects.create_user(
            username='cliente_integracion',
            email='integracion@test.com',
            password='testpass123'
        )

        cls.tipo_seguro = TipoSeguro.objects.create(
            nombre='Seguro Integración',
            comision_porcentaje=Decimal('10.00'),
            porcentaje_iva=Decimal('19.00')
        )

        cls.compania = CompaniaAseguradora.objects.create(
            nombre='Compañía Integración'
        )

    def test_poliza_mensual_genera_cuotas(self):
        """Verifica que una póliza mensual genera las cuotas correctas."""
        poliza = Poliza.objects.create(
            cliente=self.cliente,
            tipo_seguro=self.tipo_seguro,
            compania_aseguradora=self.compania,
            numero_poliza='POL-INT-001',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=365),
            valor_prima_sin_iva=Decimal('600000.00'),
            modo_pago='MENSUAL',
            plazo_meses=6
        )

        cuotas = Cuota.objects.filter(poliza=poliza)
        self.assertEqual(cuotas.count(), 6)

        # Verificar monto de cada cuota
        monto_esperado = Decimal('600000.00') / 6  # 100,000
        for cuota in cuotas:
            self.assertEqual(cuota.monto_cuota, monto_esperado)

    def test_pago_cuota_genera_comision(self):
        """Verifica que pagar una cuota genera la comisión correcta."""
        poliza = Poliza.objects.create(
            cliente=self.cliente,
            tipo_seguro=self.tipo_seguro,
            compania_aseguradora=self.compania,
            numero_poliza='POL-INT-002',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=365),
            valor_prima_sin_iva=Decimal('1200000.00'),
            modo_pago='MENSUAL',
            plazo_meses=12
        )

        cuota = Cuota.objects.filter(poliza=poliza).first()
        monto_cuota = cuota.monto_cuota  # 100,000

        # Simular pago de cuota
        cuota.estado = 'PAGADA'
        cuota.save()

        # Crear pago de comisión (10% del monto de la cuota)
        comision = monto_cuota * Decimal('0.10')
        pago = Pago.objects.create(
            poliza=poliza,
            cuota=cuota,
            fecha_pago=date.today(),
            monto_pagado=comision,
            estado_comision='PENDIENTE'
        )

        # Verificar que la comisión es correcta
        self.assertEqual(pago.monto_pagado, Decimal('10000.00'))  # 100,000 * 10%

    def test_total_comisiones_poliza_mensual(self):
        """Verifica que el total de comisiones es correcto para póliza mensual."""
        poliza = Poliza.objects.create(
            cliente=self.cliente,
            tipo_seguro=self.tipo_seguro,
            compania_aseguradora=self.compania,
            numero_poliza='POL-INT-003',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=365),
            valor_prima_sin_iva=Decimal('1000000.00'),
            modo_pago='MENSUAL',
            plazo_meses=10
        )

        # Simular pago de todas las cuotas
        cuotas = Cuota.objects.filter(poliza=poliza)
        total_comisiones = Decimal('0')

        for cuota in cuotas:
            cuota.estado = 'PAGADA'
            cuota.save()

            comision = cuota.monto_cuota * Decimal('0.10')
            Pago.objects.create(
                poliza=poliza,
                cuota=cuota,
                fecha_pago=date.today(),
                monto_pagado=comision
            )
            total_comisiones += comision

        # Verificar total
        # Prima: 1,000,000, Comisión total: 1,000,000 * 10% = 100,000
        self.assertEqual(total_comisiones, Decimal('100000.00'))
