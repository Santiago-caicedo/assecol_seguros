# reportes/templatetags/reportes_extras.py

from django import template

register = template.Library()

@register.filter
def getItem(dictionary, key):
    # Restamos 1 porque los meses vienen de 1-12 pero el índice de la lista es 0-11
    # Y devolvemos el segundo elemento de la tupla, que es el nombre del mes
    try:
        return dictionary[int(key) - 1][1]
    except (IndexError, TypeError, KeyError):
        return None