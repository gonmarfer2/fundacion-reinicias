from django import forms
from main.models import Person, User
from .models import CourseUnit, Course, CourseUnitResource
from django.contrib.auth.forms import UserCreationForm

class StudentRegisterForm(UserCreationForm):
    username = forms.CharField(max_length=30,label='Nombre de usuario')
    birth_date = forms.DateField(label='Fecha de nacimiento',widget=forms.DateInput(attrs={'type':'date'},format='%Y/%m/%d'))
    password1 = forms.CharField(label='Contraseña',max_length=190,widget=forms.PasswordInput)
    password2 = forms.CharField(max_length=190,label='Repetir contraseña',widget=forms.PasswordInput)
    name = forms.CharField(max_length=255,label='Nombre')
    last_name = forms.CharField(max_length=255,label='Apellidos')
    email = forms.EmailField(label='Correo electrónico')
    telephone = forms.RegexField(regex=r"^\+?1?\d{9,15}$",label='Teléfono')
    sex = forms.ChoiceField(choices=Person.SEX_CHOICES,label='Sexo')

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class CourseUnitCreateForm(forms.ModelForm):
    class Meta:
        model = CourseUnit
        fields = ['title']

class CourseUnitEditForm(forms.ModelForm):
    class Meta:
        model = CourseUnit
        fields = ['title','order','course']
        widgets = {
            'order': forms.NumberInput(attrs={'min':'1','type':'number'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order'].widget.attrs['min'] = 1

class CourseCreateForm(forms.Form):
    predecessors = Course.objects.all().order_by('name')

    name = forms.CharField(max_length=256,label='Nombre')
    duration = forms.DecimalField(widget=forms.NumberInput(attrs={'step':1,'min':1}),label='Duración (semanas)')
    description = forms.CharField(widget=forms.Textarea,label='Descripción')
    # This line creates problems with makemigrations
    preceeded_by = forms.ModelMultipleChoiceField(queryset=predecessors,label='Predecesores',widget=forms.CheckboxSelectMultiple, required=False)
    index_document = forms.FileField(label='Documento de curso',required=False,widget=forms.FileInput)
    published = forms.BooleanField(label='Publicado',widget=forms.CheckboxInput,required=False)

class CourseUnitResourceCreateForm(forms.ModelForm):
    class Meta:
        model = CourseUnitResource
        fields = ['resource']
