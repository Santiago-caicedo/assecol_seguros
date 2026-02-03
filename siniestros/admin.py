# siniestros/admin.py

from django.contrib import admin
from .models import TipoSiniestro, SubtipoSiniestro, Siniestro, DocumentoSiniestro, FotoSiniestro

@admin.register(TipoSiniestro)
class TipoSiniestroAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(SubtipoSiniestro)
class SubtipoSiniestroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo') # Mostramos a qué categoría pertenece
    list_filter = ('tipo',)

# Opcional: registrar los otros modelos para tener una visión completa
admin.site.register(Siniestro)
admin.site.register(DocumentoSiniestro)
admin.site.register(FotoSiniestro)