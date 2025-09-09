# polizas/forms.py
from django import forms
from .models import Poliza

class PolicyForm(forms.ModelForm):
    class Meta:
        model = Poliza
        # Lista completa de campos que el usuario debe llenar
        fields = [
            'numero_poliza',
            'compania_aseguradora',
            'tipo_seguro',
            'vehiculo', # Incluimos el campo vehículo
            'valor_prima_sin_iva', # Usamos el nuevo campo de prima
            'fecha_inicio',
            'fecha_fin',
            'poliza_pdf',
            'modo_pago',
            'plazo_meses'
        ]

        # Widgets para los campos de fecha
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Bucle para aplicar la clase de Bootstrap a todos los campos
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

        # Hacemos que el campo vehículo no sea obligatorio en el formulario
        self.fields['vehiculo'].required = False