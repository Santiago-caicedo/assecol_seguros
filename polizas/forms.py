# polizas/forms.py
from django import forms
from .models import Poliza


class SeparadorMilesInput(forms.TextInput):
    """
    Input de texto para montos en pesos: permite mostrar separadores de miles
    (ej: 1.000.000) y, al recibir el valor en el POST, elimina los separadores
    y decimales para que el DecimalField lo pueda interpretar como entero.
    """
    def value_from_datadict(self, data, files, name):
        value = super().value_from_datadict(data, files, name)
        if isinstance(value, str) and value.strip():
            # Quitamos todo lo que no sea dígito (puntos, comas, espacios, '$').
            value = ''.join(ch for ch in value if ch.isdigit())
        return value


class PolicyForm(forms.ModelForm):
    dejar_pendiente = forms.BooleanField(
        required=False,
        label='Dejar modalidad de pago pendiente por definir',
        help_text='Marca esta opción si el cliente aún no ha decidido la modalidad de pago. '
                  'La póliza quedará resaltada como pendiente hasta que la definas.',
    )

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
            'valor_prima_sin_iva': SeparadorMilesInput(attrs={
                'inputmode': 'numeric',
                'autocomplete': 'off',
                'placeholder': 'Ej: 1.000.000',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Aplicamos la clase de Bootstrap a todos los campos
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

        # El checkbox usa su propio estilo, no 'form-control'
        self.fields['dejar_pendiente'].widget.attrs.update({'class': 'form-check-input'})

        # Hacemos que el campo vehículo y asesor no sean obligatorios
        self.fields['vehiculo'].required = False
        self.fields['asesor'].required = False
        self.fields['financiera'].required = False
        self.fields['numero_credito'].required = False
        self.fields['fecha_pago_contado'].required = False
        # La modalidad puede quedar pendiente, así que no es obligatoria a nivel de campo;
        # su obligatoriedad se valida en clean() según el checkbox.
        self.fields['modo_pago'].required = False
        # El desplegable solo ofrece las modalidades reales; "pendiente" se marca con el checkbox.
        self.fields['modo_pago'].choices = [
            (valor, etiqueta) for valor, etiqueta in Poliza.MODO_PAGO_CHOICES
            if valor != 'PENDIENTE'
        ]

        # Si estamos editando una póliza que ya está pendiente, marcamos el checkbox.
        if self.instance and self.instance.pk and self.instance.modo_pago == 'PENDIENTE':
            self.fields['dejar_pendiente'].initial = True

        # Al editar, mostramos la prima como entero (sin decimales) para que el
        # formateo de miles del lado del cliente quede limpio (ej: 1.000.000).
        if self.instance and self.instance.pk and self.instance.valor_prima_sin_iva is not None:
            self.initial['valor_prima_sin_iva'] = int(self.instance.valor_prima_sin_iva)

    def clean(self):
        cleaned_data = super().clean()

        dejar_pendiente = cleaned_data.get('dejar_pendiente')
        financiera = cleaned_data.get('financiera')
        numero_credito = cleaned_data.get('numero_credito')
        fecha_pago_contado = cleaned_data.get('fecha_pago_contado')
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        valor_prima = cleaned_data.get('valor_prima_sin_iva')
        plazo_meses = cleaned_data.get('plazo_meses')

        # --- Validaciones núcleo: aplican SIEMPRE, incluso si la modalidad queda pendiente ---
        if fecha_inicio and fecha_fin and fecha_fin <= fecha_inicio:
            self.add_error('fecha_fin', 'La fecha de fin debe ser posterior a la fecha de inicio.')

        if valor_prima is not None and valor_prima <= 0:
            self.add_error('valor_prima_sin_iva', 'El valor de la prima debe ser mayor a cero.')

        # Si se marca "dejar pendiente", la modalidad queda sin definir y se
        # omiten las validaciones ESPECÍFICAS de modalidad (plazo, financiera, fecha de pago).
        if dejar_pendiente:
            cleaned_data['modo_pago'] = 'PENDIENTE'
            return cleaned_data

        modo_pago = cleaned_data.get('modo_pago')

        if not modo_pago or modo_pago == 'PENDIENTE':
            self.add_error(
                'modo_pago',
                'Selecciona una modalidad de pago o marca "Dejar pendiente por definir".'
            )

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