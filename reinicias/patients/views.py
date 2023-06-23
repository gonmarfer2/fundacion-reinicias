from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from main.views import group_required
from django.http import Http404
from main.models import Person
from .models import Diary, DiaryEntry
from technics.models import Patient
from django.core.paginator import Paginator
from django.db import transaction
from .forms import DiaryEntryCreationForm
from django.core.exceptions import PermissionDenied

# Constants
ERROR_404_PERSON = 'Ese usuario no existe'

@require_http_methods(["GET"])
@group_required("technics","patients")
def show_diary(request,person_id):
    this_patient = Patient.objects.filter(person__pk=person_id)
    if not this_patient.exists():
        raise Http404(ERROR_404_PERSON)
    
    this_patient = this_patient.first()
    if not request.user.is_superuser and request.user.get_person().pk != person_id:
        raise PermissionDenied
    this_diary = Diary.objects.get(patient=this_patient)

    diary_entries = DiaryEntry.objects.filter(diary=this_diary).order_by('-datetime')
    paginator = Paginator(diary_entries,5)

    page_number = request.GET.get('page',None)
    page_obj = paginator.get_page(page_number)

    context = {
        'userGroups':request.user.groups.all(),
        'diary':this_diary,
        'entries':page_obj,
        'pages': {
            'current':int(page_obj.number),
            'has_previous':page_obj.has_previous(),
            'has_next':page_obj.has_next()
        }
    }

    return render(request,'diary/show.html',context)


@require_http_methods(["GET","POST"])
@group_required("patients")
@transaction.atomic()
def create_diary_entry(request,person_id):
    this_patient = Patient.objects.filter(person__pk=person_id)
    if not this_patient.exists():
        raise Http404(ERROR_404_PERSON)
    
    this_patient = this_patient.first()
    this_diary = Diary.objects.get(patient=this_patient)

    form = DiaryEntryCreationForm()

    if request.method == 'POST':
        form = DiaryEntryCreationForm(request.POST)

        if form.is_valid():
            new_entry = form.save(commit=False)
            new_entry.diary = this_diary
            new_entry.save()

            return redirect(f'/patients/diary/{this_patient.person.pk}')
    
    context = {
        'userGroups':request.user.groups.all(),
        'form':form
    }

    return render(request,'diary/create.html',context)