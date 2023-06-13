from django import forms
from main.models import Person, User
from .models import PatientRecord, PatientRecordDocument, PatientRecordHistory
from django.contrib.auth.forms import UserChangeForm

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