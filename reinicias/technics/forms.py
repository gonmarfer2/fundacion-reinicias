from typing import Any, Dict
from django import forms
from main.models import Person, User, Technic
from .models import Session, Patient, PatientRecord, PatientRecordDocument, PatientRecordHistory, SessionNote, InitialReport
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta

USER_NAME_LABEL = 'Nombre de usuario'
USER_BIRTH_LABEL = 'Fecha de nacimiento'
USER_EMAIL_LABEL = 'Correo electrónico'
USER_TELEPHONE_REGEX = r"^\+?1?\d{9,15}$"
USER_TELEPHONE_LABEL = 'Teléfono'

class MemberEditForm(UserChangeForm):
    username = forms.CharField(max_length=30,label=USER_NAME_LABEL,widget=forms.TextInput(attrs={'readonly':True}))
    birth_date = forms.DateField(label=USER_BIRTH_LABEL,widget=forms.DateInput(attrs={'type':'date'},format='%Y-%m-%d'))
    name = forms.CharField(max_length=255,label='Nombre')
    last_name = forms.CharField(max_length=255,label='Apellidos')
    email = forms.EmailField(label=USER_EMAIL_LABEL)
    telephone = forms.RegexField(regex=USER_TELEPHONE_REGEX,label=USER_TELEPHONE_LABEL)
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
            self.fields['record_state'] = forms.ChoiceField(choices=PatientRecordHistory.RECORD_STATES,label='Estado del expediente')

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
    username = forms.CharField(max_length=30,label=USER_NAME_LABEL)
    birth_date = forms.DateField(label=USER_BIRTH_LABEL,widget=forms.DateInput(attrs={'type':'date'},format='%Y/%m/%d'))
    password1 = forms.CharField(label='Contraseña',max_length=190,widget=forms.PasswordInput)
    password2 = forms.CharField(max_length=190,label='Repetir contraseña',widget=forms.PasswordInput)
    name = forms.CharField(max_length=255,label='Nombre')
    last_name = forms.CharField(max_length=255,label='Apellidos')
    email = forms.EmailField(label=USER_EMAIL_LABEL)
    telephone = forms.RegexField(regex=USER_TELEPHONE_REGEX,label=USER_TELEPHONE_LABEL)
    sex = forms.ChoiceField(choices=Person.SEX_CHOICES,label='Sexo')
    roles = forms.MultipleChoiceField(choices=(
                    ('teachers','Formador'),
                    ('technics','Técnico')
                ),label='Selecciona los roles',widget=forms.CheckboxSelectMultiple())

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


def clean_session_forms(this_form):
    # Date not coincides for technic and patient(s)
    this_date = this_form.cleaned_data.get('date')
    this_time = this_form.cleaned_data.get('time')

    aux_time = datetime(2000,1,1,this_time.hour,this_time.minute)
    this_time_lower_bound = (aux_time - timedelta(minutes=5)).time()
    this_time_upper_bound = (aux_time + timedelta(minutes=5)).time()

    this_technic = this_form.cleaned_data.get('technic')
    this_patient = this_form.cleaned_data.get('patient',[])

    session_exists_technic = Session.objects.exclude(pk=this_form.instance.pk).filter(technic=this_technic,datetime__date=this_date,datetime__time__gte=this_time_lower_bound,datetime__time__lte=this_time_upper_bound).exists()
    if session_exists_technic:
        raise ValidationError(
            "Ya existe una sesión para ese técnico en esa fecha y hora.",
            code="already_session_technic"
        )
    
    if len(this_patient) > 0:
        session_exists_patient = Session.objects.exclude(pk=this_form.instance.pk).filter(patient__in=this_patient,datetime__date=this_date,datetime__time__gte=this_time_lower_bound,datetime__time__lte=this_time_upper_bound).exists()
        if session_exists_patient:
            raise ValidationError(
                "Ya existe una sesión para los pacientes seleccionados en esa fecha y hora.",
                code="already_session_patients"
            )

    # Patient clean
    patient_list = this_form.cleaned_data.get('patient',[])

    is_initial = this_form.cleaned_data.get('is_initial')
    if is_initial and len(patient_list) > 0:
        raise ValidationError(
            "Si la sesión es inicial, no se pueden seleccionar pacientes.",
            code="initial_no_patient"
        )

    session_type = this_form.cleaned_data.get('session_type')
    if not is_initial and (session_type == 'i' or session_type == 'f') and len(patient_list) != 1:
        raise ValidationError(
            "Si la sesión es individual o familiar, debe seleccionarse solo un paciente.",
            code="individual_one_patient"
        )
    
    if not is_initial and session_type == 'g' and len(patient_list) < 2:
        raise ValidationError(
            "Si la sesión es grupal, deben seleccionarse, al menos, dos pacientes.",
            code="groupal_two_patients"
        )


class SessionCreateForm(forms.ModelForm):

    date = forms.DateField(label='Fecha',widget=forms.DateInput(format='%d/%m/%Y',attrs={'type':'date'}))
    time = forms.TimeField(label='Hora',widget=forms.TimeInput(format='%H:%M',attrs={'type':'time'}))
    patient = forms.ModelMultipleChoiceField(queryset=Patient.objects.all().order_by('person__name','person__last_name'),label='Paciente(s)',widget=forms.CheckboxSelectMultiple,required=False)
    is_initial = forms.BooleanField(required=False,label='Es inicial')

    class Meta:
        model = Session
        fields = ['date','time','technic','title','patient','is_initial','session_type']

    def clean(self):
        super().clean()
        # Datetime clean // Commented out in case it's necessary in the future
        '''session_datetime = datetime.strptime(f'{self.cleaned_data.get("date")} {self.cleaned_data.get("time")}','%Y-%m-%d %H:%M:%S')
        if (session_datetime + timedelta(minutes=2)) < datetime.now():
            raise ValidationError(
                "No se pueden crear sesiones anteriores a la fecha actual.",
                code="sessions_after_now"
            )'''
        
        clean_session_forms(self)


class SessionEditForm(forms.ModelForm):

    date = forms.DateField(label='Fecha',widget=forms.DateInput(format='%d/%m/%Y',attrs={'type':'date'}))
    time = forms.TimeField(label='Hora',widget=forms.TimeInput(format='%H:%M',attrs={'type':'time'}))
    patient = forms.ModelMultipleChoiceField(queryset=Patient.objects.all().order_by('person__name','person__last_name'),label='Paciente(s)',widget=forms.CheckboxSelectMultiple,required=False)
    is_initial = forms.BooleanField(required=False,label='Es inicial')

    class Meta:
        model = Session
        fields = ['date','time','technic','title','patient','is_initial','session_type','session_state']

    def __init__(self,*args,**kwargs):
        disabled = kwargs.pop('disabled',False)
        self.request = kwargs.pop('request',None)
        super().__init__(*args,**kwargs)

        if disabled:
            self.fields['patient'].queryset = self.instance.patient.all()
            self.fields['patient'].widget.choices = self.fields['patient'].choices
            for field in self.fields:
                self.fields[field].widget.attrs['disabled'] = True

    def clean(self):
        super().clean()

        clean_session_forms(self)


class NoteCreateForm(forms.ModelForm):
    
    class Meta:
        model = SessionNote
        fields = ['text']


class InitialReportCreateForm(forms.ModelForm):

    class Meta:
        model = InitialReport
        fields = ['record_number','initial_problem','name','last_name',
                  'treatment_type','first_evaluation','family_situation',
                  'social_situation','academic_situation','problem_situation',
                  'drug_history','leisure','labour_situation','social_diagnostic',
                  'answer_plan','observations']
        
    def __init__(self,*args,**kwargs):
        disabled = kwargs.pop('disabled',False)
        self.session_id = kwargs.pop('session_id',None)
        super().__init__(*args,**kwargs)

        if disabled:
            for field in self.fields:
                self.fields[field].widget.attrs['disabled'] = True

    def clean(self):
        super().clean()

        if self.session_id and not self.instance:
            reports_for_session = Session.objects.filter(pk=self.session_id)
            if reports_for_session.count() != 0:
                raise ValidationError(
                    "Ya existe un informe para la misma sesión",
                    code='duplicate_report'
                )
            

class PatientCreateForm(UserCreationForm):
    username = forms.CharField(max_length=30,label=USER_NAME_LABEL)
    birth_date = forms.DateField(label=USER_BIRTH_LABEL,widget=forms.DateInput(attrs={'type':'date'},format='%Y/%m/%d'))
    password1 = forms.CharField(label='Contraseña',max_length=190,widget=forms.PasswordInput)
    password2 = forms.CharField(max_length=190,label='Repetir contraseña',widget=forms.PasswordInput)
    name = forms.CharField(required=False,max_length=255,label='Nombre',widget=forms.TextInput(attrs={'readonly':True}))
    last_name = forms.CharField(required=False,max_length=255,label='Apellidos',widget=forms.TextInput(attrs={'readonly':True}))
    email = forms.EmailField(label=USER_EMAIL_LABEL)
    telephone = forms.RegexField(regex=USER_TELEPHONE_REGEX,label=USER_TELEPHONE_LABEL)
    sex = forms.ChoiceField(choices=Person.SEX_CHOICES,label='Sexo')
    roles = forms.CharField(required=False,max_length=255,label='Rol',widget=forms.TextInput(attrs={'readonly':True}))
    school = forms.CharField(max_length=4096,label='Centro escolar')

    class Meta:
        model = User
        fields = ['username','birth_date','password1','password2','name','last_name','email','telephone','sex','roles']
