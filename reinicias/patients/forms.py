from django import forms
from django.core.exceptions import ValidationError
from .models import DiaryEntry, Task, Delivery, DeliveryDocument

class DiaryEntryCreationForm(forms.ModelForm):

    class Meta:
        model = DiaryEntry
        fields = ['title','content','feeling']


class TaskCreationForm(forms.ModelForm):

    deadline = forms.DateField(label='Fecha de entrega',widget=forms.DateInput(attrs={'type':'date'},format='%Y-%m-%d'))

    class Meta:
        model = Task
        fields = ['title','description','deadline']


class DeliveryCreationForm(forms.Form):
    text = forms.CharField(required=False,widget=forms.Textarea,label='Entrega de texto')
    documents = forms.FileField(required=False,widget=forms.ClearableFileInput(attrs={'multiple':True}),label='Entrega de documentos')