from django.contrib import admin
from .models import TipoSeguro, Poliza, CompaniaAseguradora

@admin.register(CompaniaAseguradora)
class CompaniaAseguradoraAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(TipoSeguro)
class TipoSeguroAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Poliza)
class PolizaAdmin(admin.ModelAdmin):
    """
    Configuración del admin para Pólizas (versión corregida).
    """
    # 👇 LÍNEA CORREGIDA 👇
    # Usamos el nuevo campo 'estado' en lugar de 'esta_activa' y 'esta_vencida'
    list_display = ('numero_poliza', 'cliente', 'compania_aseguradora', 'tipo_seguro', 'fecha_fin', 'estado', 'modo_pago')

    # 👇 LÍNEA CORREGIDA 👇
    # Filtramos por el nuevo campo 'estado'
    list_filter = ('estado', 'tipo_seguro', 'compania_aseguradora', 'modo_pago')

    search_fields = ('numero_poliza', 'cliente__username', 'cliente__first_name', 'cliente__last_name')
    date_hierarchy = 'fecha_fin'
    ordering = ('-fecha_fin',)
    list_per_page = 20
    # Añadimos los nuevos campos al editor para que sean visibles
    fieldsets = (
        ('Información Principal', {
            'fields': ('numero_poliza', 'cliente', 'compania_aseguradora', 'tipo_seguro', 'fecha_inicio', 'fecha_fin', 'poliza_pdf')
        }),
        ('Detalles Financieros y de Pago', {
            # 👇 Limpiamos los campos que se muestran 👇
            'fields': ('prima_total', 'modo_pago', 'plazo_meses')
        }),
        
    )