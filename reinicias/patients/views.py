from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from main.views import group_required
from django.http import Http404
from main.models import Person
from .models import Diary, DiaryEntry, FEELINGS
from technics.models import Patient
from django.core.paginator import Paginator
from django.db import transaction
from .forms import DiaryEntryCreationForm
from django.core.exceptions import PermissionDenied
import plotly.express as px
from datetime import datetime, timedelta, timezone

# Constants
ERROR_404_PERSON = 'Ese usuario no existe'

FEELINGS_TRANSLATION = {f:feeling for f,feeling in FEELINGS}
FEELINGS_TO_COLORS = {
    'Ira':'#ee6131',
    'Agresividad':'#ee6131',
    'Frustración':'#ee6131',
    'Miedo':'#d76ec0',
    'Humillación':'#d76ec0',
    'Rechazo':'#d76ec0',
    'Ansiedad':'#d76ec0',
    'Alegría':'#ffbb93',
    'Euforia':'#ffbb93',
    'Respeto':'#ffbb93',
    'Satisfacción':'#ffbb93',
    'Tristeza':'#09a5d4',
    'Aburrimiento':'#09a5d4',
    'Soledad':'#09a5d4',
    'Depresión':'#09a5d4',
    'Culpabilidad':'#09a5d4',
    'Ignorancia':'#09a5d4',
    'Vergüenza':'#09a5d4'
}

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


@require_http_methods(["GET"])
@group_required("technics","patients")
def show_feelings(request,person_id):
    this_patient = Patient.objects.filter(person__pk=person_id)
    if not this_patient.exists():
        raise Http404(ERROR_404_PERSON)
    
    this_patient = this_patient.first()
    this_diary = Diary.objects.get(patient=this_patient)
    
    entries = DiaryEntry.objects.filter(diary=this_diary)

    history = {}
    feelings = {}

    sorted_entries = entries.order_by('-datetime')
    paginator = Paginator(sorted_entries,5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    for e in page_obj:
        history[f'entry_{e.pk}'] = {
            'datetime':e.datetime,
            'feeling':e.feeling,
            'feeling_display':FEELINGS_TRANSLATION[e.feeling],
            'type':'Entrada de diario',
        }

    for e in sorted_entries:
        if e.datetime > (datetime.now(timezone.utc) - timedelta(days=30)):
            feeling = FEELINGS_TRANSLATION[e.feeling]
            color = FEELINGS_TO_COLORS[feeling]
            if feeling not in feelings:
                feelings[feeling] = (1,color)
            else:
                feelings[feeling] = (feelings[feeling][0]+1,color)

    feelings_chart = create_feelings_chart(feelings,FEELINGS_TO_COLORS)

    context = {
        'userGroups':request.user.groups.all(),
        'history':history,
        'feelingsChart':feelings_chart,
        'history':history,
        'pages':{
            'current':int(page_obj.number),
            'has_previous':page_obj.has_previous(),
            'has_next':page_obj.has_next()
            }
    }

    return render(request,'feelings/show.html',context)



def create_feelings_chart(feelings,feelings_to_colors):
    if len(feelings) == 0:
        return '<span>No hay datos suficientes</span>'

    feeling_values = sorted(feelings.items(),key=lambda x : (x[1][1],x[0]))
    problems_fig = px.pie(
        values=[feeling[1][0] for feeling in feeling_values],
        names=[feeling[0] for feeling in feeling_values],
        color_discrete_sequence=[feeling[1][1] for feeling in feeling_values],
    )

    problems_fig.update_traces(
        hoverinfo='label+value',
        hovertemplate='%{label} <br>Cantidad: %{value}',
        hoverlabel={
            'font':{'family':'OpenSans'}
        },
        textfont={
            'color':'#ffffff',
            'family':'OpenSans'
        }
    )

    problems_fig.update_layout(
        legend={
            'font':{'family':'OpenSans'}
        },
        font={
            'family':'Montserrat'
        }
    )

    return problems_fig.to_html()