from django import template

register = template.Library()

@register.filter
def calcular_comision(pago):
    """Devuelve la comisión registrada en el Pago.

    Por diseño actual, Pago.monto_pagado YA es la comisión generada (ver signal
    crear_pago_para_contado_y_credito y marcar_cuota_pagada_view), no la prima
    pagada por el cliente.
    """
    try:
        return pago.monto_pagado or 0
    except AttributeError:
        return 0