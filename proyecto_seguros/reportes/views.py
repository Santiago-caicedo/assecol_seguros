# reportes/views.py

import json
import pandas as pd
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from polizas.models import Poliza, TipoSeguro, CompaniaAseguradora
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
    fecha_seleccionada = datetime(ano_actual, mes_actual, 1)

    # --- 2. Cálculos de Métricas KPI para el Mes Seleccionado ---
    pagos_del_mes = Pago.objects.filter(
        fecha_pago__year=ano_actual,
        fecha_pago__month=mes_actual
    ).select_related('poliza__tipo_seguro')
    
    total_comisiones_mes = sum(pago.monto_pagado * (pago.poliza.tipo_seguro.comision_porcentaje / 100) for pago in pagos_del_mes)
    
    total_ventas_mes = Poliza.objects.filter(
        fecha_inicio__year=ano_actual,
        fecha_inicio__month=mes_actual
    ).aggregate(total=Sum('prima_total'))['total'] or 0

    nuevas_polizas_mes = Poliza.objects.filter(
        fecha_inicio__year=ano_actual,
        fecha_inicio__month=mes_actual
    ).count()

    # --- 3. Análisis de Crecimiento Mes a Mes (MoM) ---
    fecha_mes_anterior = fecha_seleccionada - relativedelta(months=1)
    
    pagos_mes_anterior = Pago.objects.filter(fecha_pago__year=fecha_mes_anterior.year, fecha_pago__month=fecha_mes_anterior.month).select_related('poliza__tipo_seguro')
    comisiones_mes_anterior = sum(pago.monto_pagado * (pago.poliza.tipo_seguro.comision_porcentaje / 100) for pago in pagos_mes_anterior)
    
    comision_mom_change = 0
    if comisiones_mes_anterior > 0:
        comision_mom_change = ((total_comisiones_mes - comisiones_mes_anterior) / comisiones_mes_anterior) * 100

    nuevas_polizas_mes_anterior = Poliza.objects.filter(fecha_inicio__year=fecha_mes_anterior.year, fecha_inicio__month=fecha_mes_anterior.month).count()
    
    polizas_mom_change = 0
    if nuevas_polizas_mes_anterior > 0:
        polizas_mom_change = ((nuevas_polizas_mes - nuevas_polizas_mes_anterior) / nuevas_polizas_mes_anterior) * 100

    # --- 4. Datos para Gráficos ---
    # Gráfico 1: Ventas por Tipo de Seguro
    ventas_por_tipo = Poliza.objects.filter(
        fecha_inicio__year=ano_actual,
        fecha_inicio__month=mes_actual
    ).values('tipo_seguro__nombre') \
     .annotate(total_vendido=Sum('prima_total')) \
     .order_by('-total_vendido')

    labels_grafico_tipos = [item['tipo_seguro__nombre'] for item in ventas_por_tipo]
    data_grafico_tipos = [float(item['total_vendido']) for item in ventas_por_tipo]

    # Gráfico 2: Tendencia de Comisiones (Últimos 12 meses)
    fecha_hace_12_meses = (hoy - relativedelta(months=11)).replace(day=1)
    pagos_ultimo_ano = Pago.objects.filter(fecha_pago__gte=fecha_hace_12_meses).select_related('poliza__tipo_seguro')
    
    data_para_pandas = [{
        'fecha_pago': pago.fecha_pago,
        'comision_ganada': float(pago.monto_pagado) * (float(pago.poliza.tipo_seguro.comision_porcentaje) / 100)
    } for pago in pagos_ultimo_ano]

    labels_tendencia, data_tendencia = [], []
    if data_para_pandas:
        df = pd.DataFrame(data_para_pandas)
        df['fecha_pago'] = pd.to_datetime(df['fecha_pago'])
        comisiones_mensuales = df.set_index('fecha_pago')['comision_ganada'].resample('MS').sum()
        labels_tendencia = comisiones_mensuales.index.strftime('%b %Y').tolist()
        data_tendencia = comisiones_mensuales.values.round(2).tolist()

    # --- 5. Análisis Avanzados ---
    # Análisis 1: Rendimiento por Compañía Aseguradora
    comisiones_por_compania = Poliza.objects.filter(pagos__fecha_pago__year=ano_actual, pagos__fecha_pago__month=mes_actual) \
        .annotate(compania_nombre=F('compania_aseguradora__nombre')) \
        .values('compania_nombre') \
        .annotate(total_comision=Sum(F('pagos__monto_pagado') * (F('tipo_seguro__comision_porcentaje') / 100))) \
        .order_by('-total_comision')
    labels_companias = [item['compania_nombre'] for item in comisiones_por_compania]
    data_companias = [float(item['total_comision']) for item in comisiones_por_compania]

    # Análisis 2: Top 5 Clientes
    top_clientes_qs = User.objects.filter(is_staff=False, polizas__pagos__fecha_pago__year=ano_actual, polizas__pagos__fecha_pago__month=mes_actual) \
    .annotate(total_comision_generada=Sum(F('polizas__pagos__monto_pagado') * (F('polizas__tipo_seguro__comision_porcentaje') / 100))) \
    .order_by('-total_comision_generada')[:5]

    # Procesamos la lista para redondear y preparar los datos para la plantilla
    top_clientes_list = []
    for cliente in top_clientes_qs:
        top_clientes_list.append({
            'nombre': cliente.get_full_name() or cliente.username,
            'comision': round(cliente.total_comision_generada or 0, 2)
        })

    # Análisis 3: Salud de la Cartera
    salud_cartera = Poliza.objects.filter(estado='ACTIVA').values('estado_cartera').annotate(count=Count('id'))
    labels_salud_cartera = [item['estado_cartera'].replace('_', ' ').capitalize() for item in salud_cartera]
    data_salud_cartera = [item['count'] for item in salud_cartera]

    # --- 6. Preparamos el contexto completo ---
    context = {
        'total_comisiones_mes': round(total_comisiones_mes, 2),
        'total_ventas_mes': round(total_ventas_mes, 2),
        'nuevas_polizas_mes': nuevas_polizas_mes,
        'comision_mom_change': round(comision_mom_change, 1),
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
        'top_clientes':top_clientes_list,
        'labels_salud_cartera': json.dumps(labels_salud_cartera),
        'data_salud_cartera': json.dumps(data_salud_cartera),
    }
    
    return render(request, 'reportes/panel_reportes.html', context)
