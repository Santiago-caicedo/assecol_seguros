# reportes/views.py

import json
import pandas as pd
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from polizas.models import Asesor, Poliza, TipoSeguro, CompaniaAseguradora
from cartera.models import Pago
from django.contrib.auth.models import User
from django.db.models import Sum, Count, F
from datetime import datetime
from dateutil.relativedelta import relativedelta


def es_admin(user):
    """Función de prueba para decoradores, verifica si el usuario es staff."""
    return user.is_staff


@login_required
@user_passes_test(es_admin)
def panel_reportes_view(request):
    # --- 1. Manejo de Filtros de Fecha ---
    hoy = timezone.now()
    ano_actual = int(request.GET.get('ano', hoy.year))
    mes_actual = int(request.GET.get('mes', hoy.month))

    # --- 2. Cálculos de Métricas KPI para el Mes Seleccionado ---
    polizas_del_mes = Poliza.objects.filter(
        fecha_inicio__year=ano_actual,
        fecha_inicio__month=mes_actual
    ).select_related('tipo_seguro')

    pagos_del_mes = Pago.objects.filter(
        fecha_pago__year=ano_actual,
        fecha_pago__month=mes_actual
    )

    total_ventas_con_iva = sum(p.valor_total_a_pagar for p in polizas_del_mes)
    comisiones_pendientes_mes = pagos_del_mes.filter(estado_comision='PENDIENTE').aggregate(total=Sum('monto_pagado'))['total'] or 0
    comisiones_liquidadas_mes = pagos_del_mes.filter(estado_comision='LIQUIDADA').aggregate(total=Sum('monto_pagado'))['total'] or 0
    nuevas_polizas_mes = polizas_del_mes.count()

    # --- 3. (Opcional) Análisis MoM para Nuevas Pólizas ---
    fecha_seleccionada = datetime(ano_actual, mes_actual, 1)
    fecha_mes_anterior = fecha_seleccionada - relativedelta(months=1)
    nuevas_polizas_mes_anterior = Poliza.objects.filter(fecha_inicio__year=fecha_mes_anterior.year, fecha_inicio__month=fecha_mes_anterior.month).count()
    polizas_mom_change = 0
    if nuevas_polizas_mes_anterior > 0:
        polizas_mom_change = ((nuevas_polizas_mes - nuevas_polizas_mes_anterior) / nuevas_polizas_mes_anterior) * 100


    # --- 4. Datos para Gráficos y Análisis Avanzados ---
    # Gráfico 1: Ventas por Tipo de Seguro (base sin IVA)
    ventas_por_tipo = polizas_del_mes.values('tipo_seguro__nombre') \
     .annotate(total_vendido=Sum('valor_prima_sin_iva')) \
     .order_by('-total_vendido')
    labels_grafico_tipos = [item['tipo_seguro__nombre'] for item in ventas_por_tipo]
    data_grafico_tipos = [float(item['total_vendido']) for item in ventas_por_tipo]

    # Gráfico 2: Tendencia de Comisiones (Últimos 12 meses)
    fecha_hace_12_meses = (hoy - relativedelta(months=11)).replace(day=1)
    pagos_ultimo_ano = Pago.objects.filter(fecha_pago__gte=fecha_hace_12_meses).select_related('poliza__tipo_seguro')
    
    data_para_pandas = [{'fecha_pago': pago.fecha_pago, 'comision_ganada': pago.monto_pagado} for pago in pagos_ultimo_ano]
    labels_tendencia, data_tendencia = [], []
    if data_para_pandas:
        df = pd.DataFrame(data_para_pandas)
        df['fecha_pago'] = pd.to_datetime(df['fecha_pago'])
        # Convertimos la columna a tipo numérico, forzando errores a NaN, y luego rellenamos con 0
        df['comision_ganada'] = pd.to_numeric(df['comision_ganada'], errors='coerce').fillna(0)
        comisiones_mensuales = df.set_index('fecha_pago')['comision_ganada'].resample('MS').sum()
        labels_tendencia = comisiones_mensuales.index.strftime('%b %Y').tolist()
        data_tendencia = comisiones_mensuales.values.round(2).tolist()
    
    # Análisis 1: Rendimiento por Compañía Aseguradora
    comisiones_por_compania = Pago.objects.filter(fecha_pago__year=ano_actual, fecha_pago__month=mes_actual) \
        .values('poliza__compania_aseguradora__nombre') \
        .annotate(total_comision=Sum('monto_pagado')) \
        .order_by('-total_comision')
    labels_companias = [item['poliza__compania_aseguradora__nombre'] for item in comisiones_por_compania]
    data_companias = [float(item['total_comision']) for item in comisiones_por_compania]

    # Análisis 2: Top 5 Clientes
    top_clientes_qs = User.objects.filter(is_staff=False, polizas__pagos__fecha_pago__year=ano_actual, polizas__pagos__fecha_pago__month=mes_actual) \
        .annotate(total_comision_generada=Sum('polizas__pagos__monto_pagado')) \
        .order_by('-total_comision_generada')[:5]
    top_clientes_list = [{'nombre': c.get_full_name() or c.username, 'comision': round(c.total_comision_generada or 0, 2)} for c in top_clientes_qs]

    # Análisis 3: Salud de la Cartera
    salud_cartera = Poliza.objects.filter(estado='ACTIVA').values('estado_cartera').annotate(count=Count('id'))
    labels_salud_cartera = [item['estado_cartera'].replace('_', ' ').capitalize() for item in salud_cartera]
    data_salud_cartera = [item['count'] for item in salud_cartera]

    # --- 5. Preparamos el contexto completo ---
    context = {
        'total_ventas_con_iva': round(total_ventas_con_iva, 0),
        'comisiones_pendientes_mes': round(comisiones_pendientes_mes, 0),
        'comisiones_liquidadas_mes': round(comisiones_liquidadas_mes, 0),
        'nuevas_polizas_mes': nuevas_polizas_mes,
        'polizas_mom_change': round(polizas_mom_change, 1),
        'mes_seleccionado': mes_actual,
        'ano_seleccionado': ano_actual,
        'rango_anos': range(hoy.year, hoy.year - 5, -1),
        'meses': [(i, datetime(2000, i, 1).strftime('%B').capitalize()) for i in range(1, 13)],
        'labels_grafico_tipos': json.dumps(labels_grafico_tipos),
        'data_grafico_tipos': json.dumps(data_grafico_tipos),
        'labels_tendencia': json.dumps(labels_tendencia),
        'data_tendencia': json.dumps(data_tendencia),
        'labels_companias': json.dumps(labels_companias),
        'data_companias': json.dumps(data_companias),
        'top_clientes': top_clientes_list,
        'labels_salud_cartera': json.dumps(labels_salud_cartera),
        'data_salud_cartera': json.dumps(data_salud_cartera),
    }
    
    return render(request, 'reportes/panel_reportes.html', context)



@login_required
@user_passes_test(es_admin)
def reporte_asesor_view(request):
    hoy = timezone.now()

    # Obtenemos la lista de todos los asesores para el filtro
    asesores = Asesor.objects.all()

    # --- Manejo de Filtros ---
    asesor_id = request.GET.get('asesor_id')
    mes = int(request.GET.get('mes', hoy.month))
    ano = int(request.GET.get('ano', hoy.year))

    polizas_vendidas = Poliza.objects.none() # Queryset vacío por defecto
    asesor_seleccionado = None
    total_primas_vendidas = 0
    total_comisiones_generadas = 0

    if asesor_id:
        try:
            asesor_seleccionado = Asesor.objects.get(pk=asesor_id)
            polizas_vendidas = Poliza.objects.filter(
                asesor=asesor_seleccionado,
                fecha_inicio__year=ano,
                fecha_inicio__month=mes
            ).select_related('cliente', 'tipo_seguro', 'compania_aseguradora')

            # Calculamos los totales para este asesor en este periodo
            for poliza in polizas_vendidas:
                total_primas_vendidas += poliza.valor_prima_sin_iva
                total_comisiones_generadas += poliza.valor_comision
        except Asesor.DoesNotExist:
            asesor_seleccionado = None

    context = {
        'asesores': asesores,
        'polizas_vendidas': polizas_vendidas,
        'asesor_seleccionado': asesor_seleccionado,
        'total_primas_vendidas': total_primas_vendidas,
        'total_comisiones_generadas': total_comisiones_generadas,
        'mes_seleccionado': mes,
        'ano_seleccionado': ano,
        'rango_anos': range(hoy.year, hoy.year - 5, -1),
        'meses': [(i, datetime(2000, i, 1).strftime('%B').capitalize()) for i in range(1, 13)],
    }
    return render(request, 'reportes/reporte_asesor.html', context)