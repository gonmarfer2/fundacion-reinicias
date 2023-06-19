from typing import Any, Dict
from django import forms
from main.models import Person, User
from .models import Session, Patient, PatientRecord, PatientRecordDocument, PatientRecordHistory
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta

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


class SessionCreateForm(forms.ModelForm):

    date = forms.DateField(label='Fecha',widget=forms.DateInput(format='%d/%m/%Y',attrs={'type':'date'}))
    time = forms.TimeField(label='Hora',widget=forms.TimeInput(format='%H:%M',attrs={'type':'time'}))
    patient = forms.ModelMultipleChoiceField(queryset=Patient.objects.all().order_by('person__name','person__last_name'),label='Paciente(s)',widget=forms.CheckboxSelectMultiple)
    is_initial = forms.BooleanField(required=False,label='Es inicial')

    class Meta:
        model = Session
        fields = ['date','time','technic','title','patient','is_initial','session_type']

    def clean(self):
        super().clean()
        # Datetime clean
        session_datetime = datetime.strptime(f'{self.cleaned_data.get("date")} {self.cleaned_data.get("time")}','%Y-%m-%d %H:%M:%S')
        if (session_datetime + timedelta(minutes=2)) < datetime.now():
            raise ValidationError(
                "No se pueden crear sesiones anteriores a la fecha actual.",
                code="sessions_after_now"
            )

        # Patient clean
        patient_list = self.cleaned_data.get('patient')

        is_initial = self.cleaned_data.get('is_initial')
        if is_initial and len(patient_list) > 0:
            raise ValidationError(
                "Si la sesión es inicial, no se pueden seleccionar pacientes.",
                code="initial_no_patient"
            )

        session_type = self.cleaned_data.get('session_type')
        if (session_type == 'i' or session_type == 'f') and len(patient_list) != 1:
            raise ValidationError(
                "Si la sesión es individual o familiar, debe seleccionarse un paciente.",
                code="individual_one_patient"
            )
        
        if session_type == 'g' and len(patient_list) < 2:
            raise ValidationError(
                "Si la sesión es grupal, deben seleccionarse, al menos, dos pacientes.",
                code="groupal_two_patients"
            )


