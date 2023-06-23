from django import forms
from django.core.exceptions import ValidationError
from .models import DiaryEntry

class DiaryEntryCreationForm(forms.ModelForm):

    class Meta:
        model = DiaryEntry
        fields = ['title','content','feeling']