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
            'fecha_pago_contado',
        ]

        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
            'fecha_pago_contado': forms.DateInput(attrs={'type': 'date'}),
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
        self.fields['fecha_pago_contado'].required = False

    def clean(self):
        cleaned_data = super().clean()
        modo_pago = cleaned_data.get('modo_pago')
        financiera = cleaned_data.get('financiera')
        numero_credito = cleaned_data.get('numero_credito')
        fecha_pago_contado = cleaned_data.get('fecha_pago_contado')
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        valor_prima = cleaned_data.get('valor_prima_sin_iva')
        plazo_meses = cleaned_data.get('plazo_meses')

        if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
            self.add_error('fecha_fin', 'La fecha de fin debe ser posterior a la fecha de inicio.')

        if valor_prima is not None and valor_prima <= 0:
            self.add_error('valor_prima_sin_iva', 'El valor de la prima debe ser mayor a cero.')

        if modo_pago in ('CREDITO', 'MENSUAL') and (not plazo_meses or plazo_meses <= 0):
            self.add_error('plazo_meses', 'El plazo en meses debe ser mayor a cero para esta modalidad.')

        if modo_pago == 'FINANCIADO':
            if not financiera:
                self.add_error('financiera', 'Requerido cuando la modalidad es Financiado.')
            if not numero_credito:
                self.add_error('numero_credito', 'Requerido cuando la modalidad es Financiado.')

        if modo_pago == 'CONTADO' and not fecha_pago_contado:
            self.add_error('fecha_pago_contado', 'Requerido cuando la modalidad es De Contado.')

        return cleaned_data