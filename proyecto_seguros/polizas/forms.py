# polizas/forms.py
from django import forms
from .models import Poliza

class PolicyForm(forms.ModelForm):
    class Meta:
        model = Poliza
        # Excluimos 'cliente' porque lo asignaremos automáticamente en la vista.
        # También 'esta_activa' que tiene un valor por defecto.
        exclude = ['cliente', 'estado', 'estado_cartera']

        # Personalizamos los widgets para que usen los selectores de fecha de HTML5
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Añadimos clases de Bootstrap a todos los campos para un buen estilo
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})