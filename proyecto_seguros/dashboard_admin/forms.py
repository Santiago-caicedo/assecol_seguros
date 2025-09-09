# dashboard_admin/forms.py
from django import forms
from django.contrib.auth.models import User
from polizas.models import TipoSeguro, CompaniaAseguradora, Poliza, Vehiculo
from siniestros.models import Siniestro, SubtipoSiniestro
from siniestros.models import DocumentoSiniestro, FotoSiniestro

class ClientCreationForm(forms.ModelForm):
  
    cedula = forms.CharField(max_length=20, required=False)
    telefono = forms.CharField(max_length=20, required=False)
    direccion = forms.CharField(max_length=255, required=False)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password'].widget = forms.PasswordInput()
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        # Primero, guardamos el usuario para obtener un objeto 'user'
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            
            # El 'signal' ya creó el perfil, nosotros solo lo actualizamos.
            perfil = user.perfilcliente
            perfil.cedula = self.cleaned_data.get('cedula')
            perfil.telefono = self.cleaned_data.get('telefono')
            perfil.direccion = self.cleaned_data.get('direccion')
            perfil.save()
        return user


class ClientUpdateForm(forms.ModelForm):
    # 👇 AÑADIMOS LOS CAMPOS DEL PERFIL AQUÍ TAMBIÉN 👇
    cedula = forms.CharField(max_length=20, required=False)
    telefono = forms.CharField(max_length=20, required=False)
    direccion = forms.CharField(max_length=255, required=False)

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 👇 LÓGICA PARA CARGAR DATOS EXISTENTES DEL PERFIL 👇
        # Si el formulario se está inicializando con una instancia de usuario...
        if self.instance and hasattr(self.instance, 'perfilcliente'):
            perfil = self.instance.perfilcliente
            self.fields['cedula'].initial = perfil.cedula
            self.fields['telefono'].initial = perfil.telefono
            self.fields['direccion'].initial = perfil.direccion

        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        # Guardamos el usuario primero
        user = super().save(commit=commit)
        # 👇 AHORA GUARDAMOS LOS CAMBIOS DEL PERFIL 👇
        if commit:
            perfil = user.perfilcliente
            perfil.cedula = self.cleaned_data.get('cedula')
            perfil.telefono = self.cleaned_data.get('telefono')
            perfil.direccion = self.cleaned_data.get('direccion')
            perfil.save()
        return user


class TipoSeguroForm(forms.ModelForm):
    class Meta:
        model = TipoSeguro
        fields = ('nombre', 'descripcion', 'comision_porcentaje', 'porcentaje_iva')


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalización de campos
        self.fields['nombre'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Ej: Seguro de Vida'})
        self.fields['descripcion'].widget.attrs.update({'class': 'form-control', 'rows': 4, 'placeholder': 'Describe brevemente en qué consiste este tipo de seguro.'})
        self.fields['comision_porcentaje'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Ej: 15.00'})
        self.fields['porcentaje_iva'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Ej: 19.00'})


class CompaniaAseguradoraForm(forms.ModelForm):
    class Meta:
        model = CompaniaAseguradora
        fields = ['nombre']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nombre'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Ej: Seguros Sura'
        })
    


class CancelPolicyForm(forms.ModelForm):
    class Meta:
        model = Poliza
        # El único campo que el admin llenará es el motivo
        fields = ['motivo_cancelacion']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['motivo_cancelacion'].widget.attrs.update({
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Describe el motivo por el cual se cancela la póliza...'
        })
        self.fields['motivo_cancelacion'].required = True



class VehiculoForm(forms.ModelForm):
    class Meta:
        model = Vehiculo
        fields = ['cliente', 'placa', 'marca', 'modelo', 'ano', 'soat_vencimiento_recordatorio']
        widgets = {
            'soat_vencimiento_recordatorio': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostramos solo clientes, no administradores
        self.fields['cliente'].queryset = User.objects.filter(is_staff=False)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})



class SiniestroForm(forms.ModelForm):
    # Le decimos a Django cómo debe manejar el campo de selección múltiple
    subtipos_afectados = forms.ModelMultipleChoiceField(
        queryset=SubtipoSiniestro.objects.all(),
        widget=forms.CheckboxSelectMultiple, # Usará checkboxes
        label="Coberturas Afectadas",
        required=True
    )

    class Meta:
        model = Siniestro
        fields = [
            'poliza', 'numero_siniestro', 'fecha_siniestro', 
            'descripcion', 'subtipos_afectados'
        ]
        widgets = {
            'fecha_siniestro': forms.DateInput(attrs={'type': 'date'}),
            'descripcion': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicamos estilos y activamos Select2 para la póliza
        self.fields['poliza'].widget.attrs.update({'class': 'form-control', 'id': 'id_poliza_siniestro'})
        self.fields['numero_siniestro'].widget.attrs.update({'class': 'form-control'})
        self.fields['fecha_siniestro'].widget.attrs.update({'class': 'form-control'})
        self.fields['descripcion'].widget.attrs.update({'class': 'form-control'})



class DocumentoSiniestroForm(forms.ModelForm):
    class Meta:
        model = DocumentoSiniestro
        fields = ['documento', 'descripcion']
        widgets = {
            'descripcion': forms.TextInput(attrs={'placeholder': 'Descripción breve del documento'}),
        }

class FotoSiniestroForm(forms.ModelForm):
    class Meta:
        model = FotoSiniestro
        fields = ['foto', 'descripcion']
        widgets = {
            'descripcion': forms.TextInput(attrs={'placeholder': 'Descripción breve de la foto'}),
        }