# polizas/forms.py
from django import forms
from .models import Poliza

class PolicyForm(forms.ModelForm):
    class Meta:
        model = Poliza
        # Lista completa de campos, incluyendo 'asesor'
        fields = [
            'numero_poliza',
            'compania_aseguradora',
            'tipo_seguro',
            'asesor', # <-- Campo añadido a la lista
            'vehiculo',
            'valor_prima_sin_iva',
            'fecha_inicio',
            'fecha_fin',
            'poliza_pdf',
            'modo_pago',
            'plazo_meses',
            'financiera',
            'numero_credito',
        ]

        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Aplicamos la clase de Bootstrap a todos los campos
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

        # Hacemos que el campo vehículo y asesor no sean obligatorios
        self.fields['vehiculo'].required = False
        self.fields['asesor'].required = False
        self.fields['financiera'].required = False
        self.fields['numero_credito'].required = False

    def clean(self):
        cleaned_data = super().clean()
        modo_pago = cleaned_data.get('modo_pago')
        financiera = cleaned_data.get('financiera')
        numero_credito = cleaned_data.get('numero_credito')

        if modo_pago == 'FINANCIADO':
            if not financiera:
                self.add_error('financiera', 'Requerido cuando la modalidad es Financiado.')
            if not numero_credito:
                self.add_error('numero_credito', 'Requerido cuando la modalidad es Financiado.')

        return cleaned_data