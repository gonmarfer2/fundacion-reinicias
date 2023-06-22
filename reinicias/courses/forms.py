from typing import Any, Dict
from django import forms
from main.models import Person, User
from .models import CourseUnit, Course, CourseUnitResource, QuestionOption, Autoevaluation
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

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

        
class CourseEditForm(forms.Form):
    
    course_id_edit = forms.IntegerField(widget=forms.HiddenInput)
    name = forms.CharField(max_length=256,label='Nombre')
    duration = forms.DecimalField(widget=forms.NumberInput(attrs={'step':1,'min':1}),label='Duración (semanas)')
    description = forms.CharField(widget=forms.Textarea,label='Descripción')
    # This line creates problems with makemigrations
    preceeded_by = forms.ModelMultipleChoiceField(queryset=Course.objects.none(),label='Predecesores',widget=forms.CheckboxSelectMultiple, required=False)
    index_document = forms.FileField(label='Documento de curso',required=False,widget=forms.FileInput)
    published = forms.BooleanField(label='Publicado',widget=forms.CheckboxInput,required=False)

    def __init__(self,*args,**kwargs):
        self.course_id = kwargs.pop('course_id_edit')
        super().__init__(*args,**kwargs)
        self.fields['course_id_edit'].initial = self.course_id
        self.fields['preceeded_by'].queryset = Course.objects.exclude(id=self.course_id).order_by('name')

    def clean(self):
        failed = []
        course_id_to_search = self.cleaned_data.get('course_id_edit')
        course = Course.objects.filter(pk=course_id_to_search)
        predecessors = self.cleaned_data.get('preceeded_by')
        if course.exists():
            for predecessor in predecessors.all():
                if course.first() in predecessor.preceeded_by.all():
                    failed.append(predecessor)
        if len(failed) > 0:
            raise ValidationError('No se puede establecer un bucle de predecesores con %(loops)s.',
                                  code='predecessor_loop',
                                  params={'loops':", ".join([f'\"{p}\"' for p in failed])})


class CourseUnitResourceCreateForm(forms.ModelForm):
    class Meta:
        model = CourseUnitResource
        fields = ['resource']


class QuestionEditForm(forms.Form):
    this_question_id = forms.IntegerField(widget=forms.HiddenInput)
    question = forms.CharField(widget=forms.Textarea,label='Pregunta')
    order = forms.IntegerField(min_value=1,label='Orden',widget=forms.NumberInput(attrs={'min':'1','step':'1'}))
    is_multiple = forms.BooleanField(label='Es de respuesta múltiple',required=False)

    def clean(self) -> Dict[str, Any]:
        qoptions = QuestionOption.objects.filter(question=self.data.get('this_question_id'))
        # Debe haber más de una opción
        if qoptions.count() < 2:
            raise ValidationError(
                'Debe haber al menos dos respuestas',
                code='min_number_answer'
            )
        # Debe haber alguna respuesta correcta

        if not qoptions.filter(is_correct=True).exists():
            raise ValidationError(
                'Debe haber al menos una respuesta correcta',
                code='min_correct_answer'
            )

        # Si el formulario es de respuesta única, no debe haber más de una respuesta correcta
        if not self.data.get('is_multiple') and qoptions.filter(is_correct=True).count() > 1:
            raise ValidationError(
                'Si la pregunta no es de respuesta múltiple, solo debe tener una respuesta correcta',
                code='no_mult_one_answer'
            )

        return super().clean()

class AutoevaluationEditForm(forms.ModelForm):
    class Meta:
        model = Autoevaluation
        fields = ['title','duration','instructions','penalization_factor']