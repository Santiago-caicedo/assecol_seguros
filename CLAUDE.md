# CLAUDE.md - Proyecto ASSECOL

## Descripción General

ASSECOL es un **Sistema de Gestión Integral de Pólizas de Seguros** desarrollado en Django. Permite administrar clientes, pólizas, cartera de pagos, comisiones, siniestros y reportes para una corredora de seguros en Colombia.

## Stack Tecnológico

| Componente | Tecnología | Versión |
|------------|------------|---------|
| Backend | Django | 5.2.4 |
| Base de Datos | PostgreSQL | - |
| Task Queue | Celery | 5.5.3 |
| Message Broker | Redis | 6.4.0 |
| Frontend | Bootstrap | 5.3.3 |
| Gráficos | Chart.js | - |
| Análisis | Pandas | 2.3.1 |
| Server WSGI | Gunicorn | 23.0.0 |

## Estructura del Proyecto

```
assecol/
├── proyecto_seguros/          # Configuración principal Django
│   ├── settings.py            # Settings (DB, Celery, Email, Logging)
│   ├── urls.py                # URLs raíz
│   ├── celery.py              # Configuración Celery
│   ├── asgi.py
│   └── wsgi.py
│
├── usuarios/                  # App: Gestión de usuarios/clientes
│   ├── models.py              # PerfilCliente (OneToOne con User)
│   ├── views.py               # PerfilClienteView, login_redirect
│   └── urls.py                # /perfil/, /redirect/
│
├── polizas/                   # App: Core del negocio
│   ├── models.py              # TipoSeguro, CompaniaAseguradora, Vehiculo, Asesor, Poliza
│   ├── signals.py             # Automatización: crear cuotas, pagos, actualizar SOAT
│   ├── tasks.py               # Celery: enviar_recordatorios_vencimiento
│   ├── forms.py               # PolicyForm
│   ├── tests.py               # Tests unitarios modelos
│   └── management/commands/
│       ├── seed_data.py       # Carga datos iniciales
│       ├── check_email_settings.py
│       └── send_test_email.py
│
├── cartera/                   # App: Gestión financiera
│   ├── models.py              # Cuota, Pago
│   ├── tests.py               # Tests unitarios cartera
│   └── management/commands/
│       └── check_cartera_status.py  # Actualiza estados de mora
│
├── dashboard_admin/           # App: Panel administrativo (controlador principal)
│   ├── views.py               # 30+ vistas (CRUD clientes, pólizas, cartera, etc.)
│   ├── forms.py               # Formularios admin
│   ├── urls.py                # 40+ endpoints bajo /dashboard/
│   └── templates/dashboard_admin/
│       ├── dashboard_home.html
│       ├── client_list.html, client_form.html
│       ├── policy_form.html, policy_confirm_cancel.html
│       ├── cartera_general.html, liquidacion_comisiones.html
│       └── ... (20+ templates)
│
├── reportes/                  # App: Análisis y KPIs
│   ├── views.py               # panel_reportes_view, reporte_asesor_view
│   ├── urls.py                # /reportes/, /reportes/rendimiento-asesor/
│   └── templates/reportes/
│       ├── panel_reportes.html
│       └── reporte_asesor.html
│
├── siniestros/                # App: Gestión de reclamaciones
│   ├── models.py              # TipoSiniestro, SubtipoSiniestro, Siniestro, Documento, Foto
│   └── admin.py
│
├── templates/
│   ├── base.html              # Template base (Bootstrap 5)
│   ├── registration/login.html
│   ├── usuarios/perfil.html
│   └── emails/                # Templates HTML para correos
│       ├── cancelacion_poliza_cliente.html
│       ├── cancelacion_poliza_admin.html
│       ├── recordatorio_vencimiento.html
│       └── recordatorio_vencimiento_admin.html
│
├── static/
│   └── css/dashboard_admin.css
│
├── media/                     # Archivos subidos
│   ├── polizas_pdf/
│   ├── comprobantes/
│   └── siniestros/
│
├── logs/                      # Logs de aplicación
│   ├── assecol.log
│   └── errors.log
│
├── manage.py
├── requirements.txt
├── .env                       # Variables de entorno
└── CLAUDE.md                  # Esta documentación
```

## Modelos de Datos

### Diagrama de Relaciones

```
User (Django)
  │
  ├── 1:1 ──► PerfilCliente (cedula, telefono, direccion)
  │
  ├── 1:N ──► Vehiculo (placa, marca, modelo, año)
  │
  └── 1:N ──► Poliza
                │
                ├── FK ──► TipoSeguro (nombre, comision_%, iva_%)
                ├── FK ──► CompaniaAseguradora (nombre)
                ├── FK ──► Asesor (nombre_completo) [opcional]
                ├── FK ──► Vehiculo [opcional]
                │
                ├── 1:N ──► Cuota (numero, fecha_vencimiento, monto, estado)
                ├── 1:N ──► Pago (fecha, monto, estado_comision)
                └── 1:N ──► Siniestro
                              │
                              ├── M:N ──► SubtipoSiniestro
                              ├── 1:N ──► DocumentoSiniestro
                              └── 1:N ──► FotoSiniestro
```

### Campos Importantes de Poliza

```python
class Poliza(models.Model):
    # Relaciones
    cliente = ForeignKey(User)
    tipo_seguro = ForeignKey(TipoSeguro)
    compania_aseguradora = ForeignKey(CompaniaAseguradora)
    vehiculo = ForeignKey(Vehiculo, null=True)  # Solo para seguros de vehículos
    asesor = ForeignKey(Asesor, null=True)

    # Información básica
    numero_poliza = CharField(unique=True)
    fecha_inicio = DateField()
    fecha_fin = DateField()
    poliza_pdf = FileField(optional)

    # Financiero
    valor_prima_sin_iva = DecimalField()

    # Modalidad de pago
    modo_pago = CharField(choices=['CONTADO', 'CREDITO', 'MENSUAL'])
    plazo_meses = PositiveIntegerField(default=12)

    # Estados
    estado = CharField(choices=['ACTIVA', 'CANCELADA', 'VENCIDA'])
    estado_cartera = CharField(choices=['AL_DIA', 'EN_MORA', 'PAGO_COMPLETO'])

    # Cancelación
    fecha_cancelacion = DateField(null=True)
    motivo_cancelacion = TextField()
    monto_devolucion = DecimalField(null=True)
    comision_devuelta = DecimalField(null=True)

    # Properties calculadas
    @property
    def valor_iva(self):
        return self.valor_prima_sin_iva * self.tipo_seguro.porcentaje_iva / 100

    @property
    def valor_total_a_pagar(self):
        return self.valor_prima_sin_iva + self.valor_iva

    @property
    def valor_comision(self):
        return self.valor_prima_sin_iva * self.tipo_seguro.comision_porcentaje / 100
```

### Estados y Transiciones

```
PÓLIZA:
  ACTIVA ──► CANCELADA (voluntario, con prorrateo si es contado)
  ACTIVA ──► VENCIDA (automático por fecha)

CARTERA:
  AL_DIA ──► EN_MORA (cuotas vencidas sin pagar)
  EN_MORA ──► AL_DIA (todas las cuotas al día)
  AL_DIA ──► PAGO_COMPLETO (todas las cuotas pagadas)

CUOTA:
  PENDIENTE ──► PAGADA (admin marca como pagada)
  PENDIENTE ──► EN_MORA (fecha vencida)
  EN_MORA ──► PAGADA (admin marca como pagada)
  PAGADA ──► PENDIENTE (admin revierte pago)

COMISIÓN (Pago):
  PENDIENTE ──► LIQUIDADA (admin liquida al asesor)
  LIQUIDADA ──► PENDIENTE (admin revierte)
```

## Flujos de Negocio

### 1. Creación de Póliza

```
Admin crea póliza en /dashboard/clientes/{id}/polizas/nueva/
         │
         ▼
    [POST form_valid]
         │
         ├── Signal: crear_pago_para_contado_y_credito
         │     └── Si CONTADO/CREDITO: Crea Pago con comisión
         │
         ├── Signal: crear_plan_de_pagos
         │     └── Si MENSUAL: Crea N Cuotas con bulk_create()
         │
         └── Signal: actualizar_recordatorio_soat
               └── Si es SOAT + tiene vehículo: Actualiza fecha recordatorio
```

### 2. Pago de Cuota (Mensual)

```
Admin en /dashboard/polizas/{id}/cartera/
         │
    [POST marcar_cuota_pagada_view]
         │
         ├── Cuota.estado = 'PAGADA'
         │
         ├── Crear Pago con comisión proporcional
         │     comision = monto_cuota * tipo_seguro.comision_% / 100
         │
         └── Evaluar estado_cartera de la póliza
               └── Si no hay cuotas EN_MORA: estado_cartera = 'AL_DIA'
```

### 3. Cancelación de Póliza

```
Admin en /dashboard/polizas/cancelar/{id}/
         │
    [GET] Muestra cálculo de prorrateo (solo CONTADO)
         │
    [POST form_valid]
         │
         ├── poliza.estado = 'CANCELADA'
         ├── poliza.fecha_cancelacion = hoy
         │
         ├── Si CONTADO:
         │     ├── Calcular prorrateo (días activos / días totales)
         │     ├── poliza.monto_devolucion = prima * (días restantes / total)
         │     ├── poliza.comision_devuelta = comision * (días restantes / total)
         │     └── Actualizar Pago con comisión real ganada
         │
         └── Enviar correos
               ├── Cliente: confirmación de cancelación
               └── Admin: notificación
```

### 4. Alertas Automáticas (Celery)

```
Celery Beat (8:00 AM diario)
         │
    [enviar_recordatorios_vencimiento]
         │
         ├── Buscar pólizas ACTIVAS que vencen en 30 días
         │
         └── Para cada póliza:
               ├── Enviar email a cliente
               └── Enviar email a admin
```

## URLs Principales

| Ruta | Vista | Descripción |
|------|-------|-------------|
| `/` | RedirectView | Redirige a login |
| `/cuentas/login/` | Django auth | Login |
| `/perfil/` | PerfilClienteView | Dashboard cliente |
| `/dashboard/` | dashboard_home_view | Home admin con alertas |
| `/dashboard/clientes/` | ClientListView | Lista clientes |
| `/dashboard/clientes/{id}/polizas/` | ClientPolicyListView | Pólizas de cliente |
| `/dashboard/polizas/cancelar/{id}/` | PolicyCancelView | Cancelar póliza |
| `/dashboard/cartera/` | CarteraGeneralView | Vista general cartera |
| `/dashboard/polizas/{id}/cartera/` | PolicyPortfolioDetailView | Detalle cartera póliza |
| `/dashboard/liquidaciones/` | LiquidacionComisionesView | Gestión comisiones |
| `/reportes/` | panel_reportes_view | KPIs y gráficos |
| `/reportes/rendimiento-asesor/` | reporte_asesor_view | Reporte por asesor |

## Roles de Usuario

```
User.is_staff = False  →  CLIENTE
  - Acceso: /perfil/
  - Ve: Sus propias pólizas, vehículos, siniestros
  - NO puede: Crear, editar, eliminar nada

User.is_staff = True   →  ADMINISTRADOR
  - Acceso: /dashboard/, /admin/
  - Ve: Todos los datos
  - Puede: CRUD completo, liquidar comisiones, cancelar pólizas
```

## Configuración

### Variables de Entorno (.env)

```bash
# Django
SECRET_KEY=tu-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos PostgreSQL
DB_NAME=assecol_db
DB_USER=postgres
DB_PASSWORD=tu-password
DB_HOST=localhost
DB_PORT=5432

# Email SMTP (SSL puerto 465)
EMAIL_HOST=smtp.tuproveedor.com
EMAIL_PORT=465
EMAIL_HOST_USER=tu@email.com
EMAIL_HOST_PASSWORD=tu-password
DEFAULT_FROM_EMAIL=ASSECOL <noreply@assecol.com>
EMAIL_ADMIN_NOTIFICACIONES=admin@assecol.com

# Redis (para Celery)
CELERY_BROKER_URL=redis://localhost:6379/0
```

### Logging

Los logs se guardan en `proyecto_seguros/logs/`:
- `assecol.log` - Todos los logs INFO+
- `errors.log` - Solo errores

Loggers configurados: `polizas`, `dashboard_admin`, `cartera`, `reportes`, `celery`

## Comandos Útiles

```bash
# Entrar al directorio del proyecto
cd proyecto_seguros

# Migraciones
python manage.py makemigrations
python manage.py migrate

# Cargar datos iniciales (compañías, tipos de seguro, siniestros)
python manage.py seed_data

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor de desarrollo
python manage.py runserver

# Ejecutar tests
python manage.py test polizas cartera -v 2

# Verificar configuración de email
python manage.py check_email_settings

# Enviar email de prueba
python manage.py send_test_email admin@example.com

# Actualizar estados de cartera (ejecutar periódicamente)
python manage.py check_cartera_status

# Celery worker (en terminal separada)
celery -A proyecto_seguros worker -l INFO

# Celery beat (programador, en otra terminal)
celery -A proyecto_seguros beat -l INFO

# Producción con Gunicorn
gunicorn proyecto_seguros.wsgi:application --bind 0.0.0.0:8000
```

## Convenciones de Código

### Nombres de Variables
- Modelos: PascalCase (`Poliza`, `TipoSeguro`)
- Campos: snake_case (`valor_prima_sin_iva`, `fecha_inicio`)
- Vistas CBV: PascalCase + sufijo (`ClientListView`, `PolicyCreateView`)
- Vistas FBV: snake_case + sufijo (`dashboard_home_view`, `marcar_cuota_pagada_view`)
- URLs: kebab-case (`/tipos-de-seguro/`, `/liquidaciones/`)

### Imports
```python
# Orden de imports
import logging                          # 1. Standard library
from decimal import Decimal

from django.shortcuts import render     # 2. Django
from django.views.generic import ListView

from polizas.models import Poliza       # 3. Local apps
from .forms import PolicyForm

logger = logging.getLogger('nombre_app')  # 4. Logger al final de imports
```

### Vistas
- Usar Class-Based Views para CRUD
- Usar Function-Based Views para acciones específicas (marcar pagada, etc.)
- Siempre usar `LoginRequiredMixin` + `UserPassesTestMixin` para proteger vistas admin
- Usar `select_related()` y `prefetch_related()` para optimizar queries

### Manejo de Errores
```python
# Usar logging, NO print()
try:
    # operación
    logger.info(f"Operación exitosa para póliza #{poliza.numero_poliza}")
except SpecificException as e:
    logger.warning(f"Caso esperado: {e}")
except Exception as e:
    logger.exception(f"Error inesperado en póliza #{poliza.numero_poliza}: {e}")
```

## Tests

### Ejecutar Tests
```bash
# Todos los tests
python manage.py test

# Tests específicos
python manage.py test polizas
python manage.py test cartera
python manage.py test polizas.tests.PolizaModelTest

# Con verbosidad
python manage.py test -v 2

# Con cobertura (requiere coverage)
coverage run manage.py test
coverage report
coverage html
```

### Estructura de Tests
```python
class PolizaModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Datos compartidos por todos los tests de la clase
        cls.cliente = User.objects.create_user(...)
        cls.tipo_seguro = TipoSeguro.objects.create(...)

    def test_valor_iva_calculo_correcto(self):
        poliza = self.crear_poliza(valor_prima_sin_iva=Decimal('1000000'))
        self.assertEqual(poliza.valor_iva, Decimal('190000'))
```

## Troubleshooting

### Error: "No module named 'polizas'"
```bash
# Asegúrate de estar en el directorio correcto
cd proyecto_seguros
python manage.py runserver
```

### Error: Conexión a PostgreSQL
```bash
# Verificar que PostgreSQL está corriendo
sudo service postgresql status

# Verificar variables de entorno
python -c "import os; print(os.environ.get('DB_NAME'))"
```

### Error: Celery no procesa tareas
```bash
# Verificar que Redis está corriendo
redis-cli ping  # Debe responder PONG

# Ejecutar worker en modo debug
celery -A proyecto_seguros worker -l DEBUG
```

### Error: Correos no se envían
```bash
# Verificar configuración
python manage.py check_email_settings

# Probar envío manual
python manage.py send_test_email tu@email.com
```

## Mejoras Pendientes (Roadmap)

### Fase 2 - Arquitectura
- [ ] Crear capa de servicios (`services.py`) para lógica de negocio
- [ ] Migrar signals a servicios explícitos
- [ ] Implementar transacciones atómicas (`@transaction.atomic`)
- [ ] Crear máquina de estados para pólizas

### Fase 3 - Performance
- [ ] Agregar índices a campos consultados frecuentemente
- [ ] Implementar paginación en reportes pesados
- [ ] Agregar cache para dashboards (Redis)

### Fase 4 - Seguridad
- [ ] Configurar HTTPS/SSL en producción
- [ ] Agregar rate limiting
- [ ] Agregar validaciones en modelos (fecha_fin > fecha_inicio, etc.)
- [ ] Implementar auditoría de cambios

---

*Última actualización: Febrero 2026*
