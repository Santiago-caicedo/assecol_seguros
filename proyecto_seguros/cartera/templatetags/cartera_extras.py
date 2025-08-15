from django import template

register = template.Library()

@register.filter
def calcular_comision(pago):
    """
    Calcula la comisión ganada para un objeto de Pago.
    Recibe un objeto 'pago' y devuelve el valor de la comisión.
    """
    try:
        comision = pago.monto_pagado * (pago.poliza.tipo_seguro.comision_porcentaje / 100)
        return comision
    except (TypeError, AttributeError):
        # En caso de que falte algún dato, devuelve 0
        return 0