from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Paciente, Turno

class BootstrapModelForm(forms.ModelForm):

    # Formulario base que inyecta automáticamente las clases de Bootstrap 5 a todos sus campos para garantizar una interfaz de usuario cuidada.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # Conservamos clases previas si las hubiera (por ejemplo si añadimos clases personalizadas)
            existing_classes = field.widget.attrs.get('class', '')
            
            # Si es un checkbox o radio de Bootstrap se maneja diferente
            if isinstance(field.widget, (forms.CheckboxInput, forms.RadioSelect)):
                field.widget.attrs.update({'class': f'{existing_classes} form-check-input'.strip()})
            else:
                field.widget.attrs.update({'class': f'{existing_classes} form-control'.strip()})

class PacienteForm(BootstrapModelForm):
    class Meta:
        model = Paciente
        fields = ['nombre', 'apellido', 'dni', 'email', 'telefono']
        # El campo 'usuario' lo asignaremos automáticamente en la vista

    def clean(self):
        """
        Delegamos la validación al modelo Paciente para evitar duplicación (DRY).
        """
        cleaned_data = super().clean()
        nombre = cleaned_data.get('nombre')
        apellido = cleaned_data.get('apellido')
        dni = cleaned_data.get('dni')
        email = cleaned_data.get('email')

        # Ejecutamos la validación centralizada en el modelo
        model_errors = Paciente.validate(nombre, apellido, dni, email)

        if model_errors:
            for error in model_errors:
                if "nombre" in error.lower():
                    self.add_error('nombre', error)
                elif "apellido" in error.lower():
                    self.add_error('apellido', error)
                elif "email" in error.lower() or "correo" in error.lower():
                    self.add_error('email', error)
                elif "dni" in error.lower():
                    self.add_error('dni', error)
                else:
                    self.add_error(None, error)  # Error global

        return cleaned_data

class TurnoForm(BootstrapModelForm):
    class Meta:
        model = Turno
        fields = ['medico', 'fecha_hora', 'motivo']
        widgets = {
            'fecha_hora': forms.TextInput(
                attrs={
                    'class': 'datetimepicker bg-white', 
                    'placeholder': 'Seleccione fecha y hora...',
                }
            ),
            'motivo': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describa brevemente el motivo de su consulta...'}),
        }

    # Validación personalizada 2
    def clean_fecha_hora(self):
        fecha = self.cleaned_data.get('fecha_hora')
        if fecha and fecha < timezone.now():
            raise ValidationError("No puedes solicitar un turno en una fecha pasada.")
        return fecha
