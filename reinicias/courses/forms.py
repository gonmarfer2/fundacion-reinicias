from django import forms
from main.models import Person, User
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