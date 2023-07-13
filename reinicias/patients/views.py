from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from main.views import group_required
from django.http import Http404, JsonResponse
from .models import Diary, DiaryEntry, FEELINGS, Task, Delivery, DeliveryDocument
from technics.models import Patient
from django.core.paginator import Paginator
from django.db import transaction
from .forms import DiaryEntryCreationForm, TaskCreationForm, DeliveryCreationForm
from django.core.exceptions import PermissionDenied
import plotly.express as px
from datetime import datetime, timedelta, timezone
from django.db.models import Q, F, CharField, Value
from django.db.models.functions import Concat
from main.models import Technic, Notification


# Constants
ERROR_404_PERSON = 'Ese usuario no existe'
ERROR_404_TASK = 'Esa tarea no existe'
ERROR_404_DELIVERY = 'No hay entregas para esa tarea'

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

@require_http_methods(['GET'])
@group_required('technics','patients')
def show_diary(request,person_id):
    this_patient = Patient.objects.filter(person__pk=person_id)
    if not this_patient.exists():
        raise Http404(ERROR_404_PERSON)
    
    this_patient = this_patient.first()
    if not (request.user.has_group('technics') or request.user.is_superuser) and request.user.get_person().pk != person_id:
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


@require_http_methods(['GET','POST'])
@group_required('patients')
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

            for technic in Technic.objects.all():
                Notification.objects.create(
                    type=f'{this_patient} ha escrito una nueva entrada en su diario.',
                    user=technic.get_user()
                )

            return redirect(f'/patients/diary/{this_patient.person.pk}')
    
    context = {
        'userGroups':request.user.groups.all(),
        'form':form
    }

    return render(request,'diary/create.html',context)


@require_http_methods(['GET'])
@group_required('technics','patients')
def show_feelings(request,person_id):
    this_patient = Patient.objects.filter(person__pk=person_id)
    if not this_patient.exists():
        raise Http404(ERROR_404_PERSON)
    
    this_patient = this_patient.first()
    this_diary = Diary.objects.get(patient=this_patient)

    if not (request.user.has_group('technics') or request.user.is_superuser) and request.user.get_person().pk != person_id:
        raise PermissionDenied
    
    entries = DiaryEntry.objects.filter(diary=this_diary).annotate(
        date=F('datetime__date'),
        type=Value('Entrada de diario',output_field=CharField()),
        ).annotate(
            new_pk=Concat(F('pk'),F('type'),output_field=CharField())
        ).values('feeling','date','type','new_pk')
    tasks = Task.objects.filter(patient=this_patient).exclude(feeling='').annotate(
        date=F('deadline'),
        type=Value('Tarea',output_field=CharField())
        ).annotate(
            new_pk=Concat(F('pk'),F('type'),output_field=CharField())
        ).values('feeling','date','type','new_pk')

    history = {}
    feelings = {}

    sorted_entries = sorted(list(entries) + list(tasks),key=lambda x : x['date'],reverse=True)
    paginator = Paginator(sorted_entries,5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    for e in page_obj:
        history[e.get("new_pk")] = {
            'datetime':e.get('date'),
            'feeling':e.get('feeling'),
            'feeling_display':FEELINGS_TRANSLATION[e.get('feeling')],
            'type':e.get('type'),
        }

    for e in sorted_entries:
        if e.get('date') >= (datetime.now(timezone.utc) - timedelta(days=30)).date():
            feeling = FEELINGS_TRANSLATION[e.get('feeling')]
            color = FEELINGS_TO_COLORS[feeling]
            if feeling not in feelings:
                feelings[feeling] = (1,color)
            else:
                feelings[feeling] = (feelings[feeling][0]+1,color)

    feelings_chart = create_feelings_chart(feelings)

    context = {
        'userGroups':request.user.groups.all(),
        'history':history,
        'feelingsChart':feelings_chart,
        'pages':{
            'current':int(page_obj.number),
            'has_previous':page_obj.has_previous(),
            'has_next':page_obj.has_next()
            }
    }

    return render(request,'feelings/show.html',context)



def create_feelings_chart(feelings):
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


@require_http_methods(['GET'])
@group_required('technics','patients')
def show_tasks_list(request,person_id):
    this_patient = Patient.objects.filter(person__pk=person_id)
    if not this_patient.exists():
        raise Http404(ERROR_404_PERSON)
    
    this_patient = this_patient.first()

    pending_tasks = Task.objects.filter(Q(state='w') | Q(state='o'),patient=this_patient).order_by('-deadline')
    sent_tasks = Task.objects.filter(state='c',patient=this_patient).order_by('-deadline')
    accepted_tasks = Task.objects.filter(state='a',patient=this_patient).order_by('-deadline')

    context = {
        'userGroups':request.user.groups.all(),
        'pendingTasks':pending_tasks,
        'sentTasks':sent_tasks,
        'acceptedTasks':accepted_tasks,
        'feelings':FEELINGS,
        'patient':this_patient
    }
    return render(request,'tasks/list.html',context)


@require_http_methods(['GET','POST'])
@group_required('technics')
@transaction.atomic()
def add_tasks(request,person_id):
    this_patient = Patient.objects.filter(person__pk=person_id)
    if not this_patient.exists():
        raise Http404(ERROR_404_PERSON)
    
    this_patient = this_patient.first()

    form = TaskCreationForm()

    if request.method == 'POST':
        form = TaskCreationForm(request.POST)

        if form.is_valid():
            new_task = form.save(commit=False)
            new_task.state = ('w')
            new_task.patient = this_patient
            new_task.technic = Technic.objects.get(person__user=request.user)
            new_task.save()

            Notification.objects.create(
                user=this_patient.get_user(),
                type=f'Tienes una tarea nueva: {new_task}'
            )

            return redirect(f'/patients/{this_patient.get_person().pk}/tasks/')
        print(form.errors)
    context = {
        'userGroups':request.user.groups.all(),
        'form':form
    }

    return render(request,'tasks/create.html',context)


@require_http_methods(['GET','POST'])
@group_required('patients')
@transaction.atomic()
def show_tasks_details(request,person_id,task_id):
    this_patient = Patient.objects.filter(person__pk=person_id)
    this_task = Task.objects.filter(pk=task_id)
    if not this_patient.exists():
        raise Http404(ERROR_404_PERSON)
    if not this_task.exists():
        raise Http404(ERROR_404_TASK)
    
    this_patient = this_patient.first()
    this_task = this_task.first()

    form = DeliveryCreationForm()

    if request.method == 'POST':
        form = DeliveryCreationForm(request.POST,request.FILES)

        if form.is_valid(): 
            data = form.cleaned_data
            
            new_delivery = Delivery(text=data.get('text'))
            new_delivery.task = this_task
            new_delivery.patient = this_patient
            new_delivery.save()

            if request.FILES.getlist('documents',None):
                for document in request.FILES.getlist('documents'):
                    new_delivery_document = DeliveryDocument(document=document)
                    new_delivery_document.delivery = new_delivery
                    new_delivery_document.save()

            this_task.state = 'c'
            this_task.save()

            for technic in Technic.objects.all():
                Notification.objects.create(
                    type=f'{this_patient} ha enviado una nueva entrega para la tarea {this_task.title}',
                    user=technic.get_user()
                )

            return redirect(f'/patients/{this_patient.get_person().pk}/tasks/')
        
    context = {
        'userGroups':request.user.groups.all(),
        'form':form,
        'task':this_task
    }

    return render(request,'tasks/delivery_send.html',context)


@require_http_methods(['GET'])
@group_required('technics','patients')
def show_delivery_details(request,person_id,task_id):
    this_patient = Patient.objects.filter(person__pk=person_id)
    this_task = Task.objects.filter(pk=task_id)
    if not this_patient.exists():
        raise Http404(ERROR_404_PERSON)
    if not this_task.exists():
        raise Http404(ERROR_404_TASK)
    
    this_patient = this_patient.first()
    this_task = this_task.first()

    this_delivery = Delivery.objects.filter(task=this_task).order_by('-datetime').first()
    if not this_delivery:
        raise Http404(ERROR_404_DELIVERY)
    
    these_docs = DeliveryDocument.objects.filter(delivery=this_delivery)
    
    context = {
        'userGroups':request.user.groups.all(),
        'delivery':this_delivery,
        'task':this_task,
        'docs':these_docs,
        'patient':this_patient
    }

    return render(request,'tasks/delivery_details.html',context)


@require_http_methods(['POST'])
@group_required('patients')
@transaction.atomic()
def evaluate_task(request,person_id,task_id):
    this_patient = Patient.objects.filter(person__pk=person_id)
    this_task = Task.objects.filter(pk=task_id)
    if not this_patient.exists():
        raise Http404(ERROR_404_PERSON)
    if not this_task.exists():
        raise Http404(ERROR_404_TASK)
    
    this_patient = this_patient.first()
    this_task = this_task.first()

    feeling = request.POST.get('feeling')

    this_task.feeling = feeling
    this_task.save()

    return JsonResponse({'response':'ok'})


@require_http_methods(['GET'])
@group_required('technics')
@transaction.atomic()
def accept_task(request,person_id,task_id):
    this_patient = Patient.objects.filter(person__pk=person_id)
    this_task = Task.objects.filter(pk=task_id)
    if not this_patient.exists():
        raise Http404(ERROR_404_PERSON)
    if not this_task.exists():
        raise Http404(ERROR_404_TASK)
    
    this_patient = this_patient.first()
    this_task = this_task.first()
    if this_task.state != 'c':
        raise PermissionDenied()

    this_task.state = 'a'
    this_task.save()

    Notification.objects.create(
        user=this_patient.get_user(),
        type=f'Se ha aceptado tu entrega para la tarea: {this_task}'
    )

    return redirect(f'/patients/{this_patient.get_person().pk}/tasks/')


@require_http_methods(['GET'])
@group_required('technics') 
@transaction.atomic()
def deny_task(request,person_id,task_id):
    this_patient = Patient.objects.filter(person__pk=person_id)
    this_task = Task.objects.filter(pk=task_id)
    if not this_patient.exists():
        raise Http404(ERROR_404_PERSON)
    if not this_task.exists():
        raise Http404(ERROR_404_TASK)
    
    this_patient = this_patient.first()
    this_task = this_task.first()
    if this_task.state != 'c':
        raise PermissionDenied()

    this_task.state = 'w'
    this_task.save()

    Notification.objects.create(
        user=this_patient.get_user(),
        type=f'Se ha rechazado tu entrega para la tarea: {this_task}'
    )

    return redirect(f'/patients/{this_patient.get_person().pk}/tasks/')


@require_http_methods(['GET'])
@group_required('technics') 
@transaction.atomic()
def delete_task(request,person_id,task_id):
    this_patient = Patient.objects.filter(person__pk=person_id)
    this_task = Task.objects.filter(pk=task_id)
    if not this_patient.exists():
        raise Http404(ERROR_404_PERSON)
    if not this_task.exists():
        raise Http404(ERROR_404_TASK)
    
    this_task.first().delete()

    return JsonResponse({'response':'ok'})

