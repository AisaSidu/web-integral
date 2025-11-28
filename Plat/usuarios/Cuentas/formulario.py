# usuarios/Cuentas/formulario.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from usuarios.models import Specialty
from .verificacion import validate_custom_password
from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV2Checkbox

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    ROLE_CHOICES = (
        ('patient', 'Paciente'),
        ('psychologist', 'Psicólogo'),
    )
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect(attrs={'class': 'role-switch'}), initial='patient')

    # campos opcionales para psicólogos (mínimos)
    phone = forms.CharField(required=False, label='Teléfono', max_length=30)
    license_number = forms.CharField(required=False, label='Número de licencia', max_length=150)
    specialties = forms.ModelMultipleChoiceField(
        queryset=Specialty.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Especialidades'
    )

    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'placeholder': 'Ingresa tu contraseña'}),
        validators=[validate_custom_password],
        help_text=None
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'placeholder': 'Repite tu contraseña'}),
        help_text=None
    )

    captcha = ReCaptchaField(
        widget=ReCaptchaV2Checkbox(
            attrs={
                'data-sitekey': '6LdhrPIrAAAAAFyE4PitYTjf2ouYhmTRHjxuNYzY',
                'data-theme': 'light',
                'data-size': 'normal',
                'class': 'g-recaptcha'
            }
        )
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'phone', 'license_number', 'specialties', 'password1', 'password2', 'captcha']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer email obligatorio y agregar clase a los campos
        self.fields['email'].required = True
        for name, field in self.fields.items():
            # dar clase y limpiar help_text
            current = field.widget.attrs.get('class', '')
            field.widget.attrs.update({
                'class': (current + ' form-input').strip(),
            })
            field.help_text = None

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este correo ya está registrado.")
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password:  # proteger contra None
            validate_custom_password(password)
        return password
