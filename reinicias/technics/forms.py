from typing import Any, Dict
from django import forms
from main.models import Person, User
from .models import PatientRecord, PatientRecordDocument, PatientRecordHistory
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.core.exceptions import ValidationError

class MemberEditForm(UserChangeForm):
    username = forms.CharField(max_length=30,label='Nombre de usuario',widget=forms.TextInput(attrs={'readonly':True}))
    birth_date = forms.DateField(label='Fecha de nacimiento',widget=forms.DateInput(attrs={'type':'date'},format='%Y-%m-%d'))
    name = forms.CharField(max_length=255,label='Nombre')
    last_name = forms.CharField(max_length=255,label='Apellidos')
    email = forms.EmailField(label='Correo electrónico')
    telephone = forms.RegexField(regex=r"^\+?1?\d{9,15}$",label='Teléfono')
    sex = forms.ChoiceField(choices=Person.SEX_CHOICES,label='Sexo')

    class Meta:
        model = User
        fields = ['username','email']

    def __init__(self, *args, **kwargs):
        roles = kwargs.pop('roles',[])
        super().__init__(*args,**kwargs)

        del self.fields['password']

        rolenames = [role.name for role in roles]
        if len(rolenames) == 1 and 'patients' in rolenames:
            self.fields['roles'] = forms.ChoiceField(choices=(('patients','Paciente'),),label='Rol',widget=forms.Select(attrs={'readonly':True}))
            self.initial['roles'] = ['patients']
        elif len(rolenames) == 1 and 'students' in rolenames:
            self.fields['roles'] = forms.ChoiceField(choices=(('students','Estudiante'),),label='Rol',widget=forms.Select(attrs={'readonly':True}))
            self.initial['roles'] = ['students']
        else:
            self.fields['roles'] = forms.MultipleChoiceField(choices=(
                    ('teachers','Formador'),
                    ('technics','Técnico')
                ),label='Selecciona los roles',widget=forms.CheckboxSelectMultiple())
            self.initial['roles'] = [role for role in rolenames]

        if 'patients' in rolenames:
            self.fields['school'] = forms.CharField(max_length=255,label='Centro educativo')

class PasswordChangeForm(forms.Form):
    password1 = forms.CharField(max_length=4096,label='Nueva contraseña',widget=forms.PasswordInput())
    password2 = forms.CharField(max_length=4096,label='Confirmar contraseña',widget=forms.PasswordInput())

    def clean(self) -> Dict[str, Any]:
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 != password2:
            raise ValidationError(
                "Las contraseñas no coinciden",
                code="unmatched_passwords"
            )
        
class MemberCreateForm(UserCreationForm):
    username = forms.CharField(max_length=30,label='Nombre de usuario')
    birth_date = forms.DateField(label='Fecha de nacimiento',widget=forms.DateInput(attrs={'type':'date'},format='%Y/%m/%d'))
    password1 = forms.CharField(label='Contraseña',max_length=190,widget=forms.PasswordInput)
    password2 = forms.CharField(max_length=190,label='Repetir contraseña',widget=forms.PasswordInput)
    name = forms.CharField(max_length=255,label='Nombre')
    last_name = forms.CharField(max_length=255,label='Apellidos')
    email = forms.EmailField(label='Correo electrónico')
    telephone = forms.RegexField(regex=r"^\+?1?\d{9,15}$",label='Teléfono')
    sex = forms.ChoiceField(choices=Person.SEX_CHOICES,label='Sexo')
    roles = forms.MultipleChoiceField(choices=(
                    ('teachers','Formador'),
                    ('technics','Técnico')
                ),label='Selecciona los roles',widget=forms.CheckboxSelectMultiple())

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']