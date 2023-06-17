from django.core.paginator import Paginator
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from main.views import group_required
from main.models import Person, Teacher, Technic, GROUP_TRANSLATION_DICTIONARY 
from .models import PatientRecord, PatientRecordDocument, PatientRecordHistory, Patient, Session, SessionNote, InitialReport, INITIAL_PROBLEMS
from django.http import Http404, JsonResponse
from .forms import MemberEditForm, PasswordChangeForm, MemberCreateForm
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q, F, Count
from django.db.models.functions import Concat
import plotly.express as px
from datetime import datetime, timezone
from django.db.models import CharField

# Constants
ERROR_404_PERSON = 'Ese usuario no existe'

@require_http_methods(["GET"])
@group_required("technics")
def show_user_list(request):
    users = Person.objects.all().order_by('user__username')
    paginator = Paginator(users,5)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'userGroups':request.user.groups.all(),
        'users':page_obj,
        'roles':{group.pk:GROUP_TRANSLATION_DICTIONARY[group.name] for group in Group.objects.all()},
        'pages':{
            'current':int(page_obj.number),
            'has_previous':page_obj.has_previous(),
            'has_next':page_obj.has_next()
            }
    }

    return render(request,'users/list.html',context)


@require_http_methods(["GET"])
@group_required("technics","patients")
def show_user_details(request,user_id):
    if Person.objects.filter(user__pk=user_id).count() == 0:
        raise Http404(ERROR_404_PERSON)
    
    this_person = Person.objects.get(pk=user_id)
    if this_person.user.has_group("patients"):
        this_person = Patient.objects.get(person=this_person)
        this_record = PatientRecord.objects.get(patient=this_person)

        this_record_documents = PatientRecordDocument.objects.filter(record=this_record)
        this_record_history = PatientRecordHistory.objects.filter(record=this_record).order_by('-start_date')
        this_creation_date = this_record_history.last().start_date
        current_state = this_record_history.first()
        initial_problem = this_record_history.filter(state='a').first()

        context = {
        'thisUser':this_person,
        'thisRecord':this_record,
        'thisRecordDocuments':this_record_documents,
        'thisRecordHistory':this_record_history,
        'createdOn':this_creation_date,
        'currentState':current_state,
        'initialProblem':initial_problem,
        'userGroups':request.user.groups.all()
        }

        return render(request,'users/details_patients.html',context)

    context = {
        'thisUser': this_person,
        'userGroups':request.user.groups.all()
    }

    return render(request,'users/details.html',context)


@require_http_methods(["GET","POST"])
@group_required("technics")
@transaction.atomic()
def edit_user(request,user_id):
    if Person.objects.filter(user__pk=user_id).count() == 0:
        raise Http404(ERROR_404_PERSON)
    
    this_person = Person.objects.get(user__id=user_id)

    initial_values = {
        'username':this_person.get_user().username,
        'birth_date':this_person.get_person().birth_date,
        'name':this_person.get_person().name,
        'last_name':this_person.get_person().last_name,
        'email':this_person.get_user().email,
        'telephone':this_person.get_person().telephone,
        'sex':this_person.get_person().sex
    }

    if this_person.user.has_group("patients"):
        this_person = Patient.objects.get(person=this_person)
        initial_values['school'] = this_person.school

    form = MemberEditForm(initial=initial_values,instance=this_person.get_user(),
    roles=this_person.get_user().groups.all())

    if request.method == "POST":
        form = MemberEditForm(request.POST,instance=this_person.get_user(),roles=this_person.get_user().groups.all())
        if form.is_valid():
            data = form.cleaned_data
            this_person.get_person().birth_date = data.get('birth_date')
            this_person.get_person().name = data.get('name')
            this_person.get_person().last_name = data.get('last_name')
            this_person.get_user().email = data.get('email')
            this_person.get_person().telephone = data.get('telephone')
            this_person.get_person().sex = data.get('sex')
            if this_person.get_user().has_group("patients"):
                this_person.school = data.get('school')

            roles = Group.objects.filter(name__in=data.get('roles'))
            if this_person.get_user().is_superuser:
                roles = Group.objects.exclude(name='students')
            this_person.get_user().groups.set(roles) 
            
            this_person.get_user().save()
            this_person.get_person().save()
            this_person.save()

            return redirect(f'/technics/users/{this_person.get_user().pk}/')

    context = {
        'thisUser':this_person,
        'form':form,
        'userGroups':request.user.groups.all()
    }

    return render(request,'users/register.html',context)


@require_http_methods(["GET","POST"])
def change_password(request,user_id):
    if Person.objects.filter(user__pk=user_id).count() == 0:
        raise Http404(ERROR_404_PERSON)
    this_person = Person.objects.get(user__id=user_id)
    if this_person.get_user() != request.user and not request.user.is_superuser:
        raise PermissionDenied()
    
    form = PasswordChangeForm()

    if request.method == "POST":
        form = PasswordChangeForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            this_person.get_user().set_password(data.get('password1'))
            this_person.get_user().save()

            return redirect(f'/technics/users/{this_person.get_user().pk}/')
        
    context = {
        'form':form,
        'userGroups':request.user.groups.all()
    }

    return render(request,'users/pass_change.html',context)


@require_http_methods(["GET","POST"])
@group_required("technics")
@transaction.atomic()
def create_member(request):
    form = MemberCreateForm()

    if request.method == "POST":
        form = MemberCreateForm(request.POST)

        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.save()

            data = form.cleaned_data
            
            for group in request.POST.getlist('roles'):
                new_user.groups.add(Group.objects.get_or_create(name=group)[0])

            new_person = Person(
                user=new_user,
                name=data.get('name'),
                last_name=data.get('last_name'),
                birth_date=data.get('birth_date'),
                telephone=data.get('telephone'),
                sex=data.get('sex')
                )
            new_person.save()

            if new_user.has_group('teachers'):
                new_teacher = Teacher(
                    person=new_person
                )
                new_teacher.save()
            
            if new_user.has_group('technics'):
                new_technic = Technic(
                    person=new_person
                )
                new_technic.save()

            return redirect(f'/technics/users/{new_user.pk}/')
    
    context = {
        'form':form,
        'userGroups':request.user.groups.all()
    }

    return render(request,'users/register.html',context)


@require_http_methods(["POST"])
@group_required("technics")
def filter_user_list(request):
    person_list = Person.objects.all().order_by('user__username')
    query_name = request.POST.get('query_name')
    if query_name:
        person_list = person_list.filter(Q(name__icontains=query_name) | Q(last_name__icontains=query_name))

    query_role = request.POST.get('query_role')
    if query_role:
        roles = Group.objects.filter(pk__in=query_role)
        person_list = person_list.filter(user__groups__in=roles)
    
    users = []
    for person in person_list:
        users.append({
            'pk':person.pk,
            'username':person.user.username,
            'full_name':str(person),
            'groups':person.user.get_groups_display(),
            'email':person.user.email
        })
    return JsonResponse({
        'users':users
    })


@require_http_methods(["GET"])
@group_required("technics")
def show_session_list(request):
    MONTHS = {
        1:'Enero',
        2:'Febrero',
        3:'Marzo',
        4:'Abril',
        5:'Mayo',
        6:'Junio',
        7:'Julio',
        8:'Agosto',
        9:'Septiembre',
        10:'Octubre',
        11:'Noviembre',
        12:'Diciembre',
    }
    SESSION_TYPES_TRANSLATION = {t:text for t,text in Session.SESSION_TYPES}
    year = request.GET.get('year')
    if year == None:
        year = datetime.now(timezone.utc).year

    reports_this_year = InitialReport.objects.filter(datetime__year=year)
    sessions_this_year = Session.objects.filter(datetime__year=year)
    PROBLEMS_TRANSLATION = {p:problem for p,problem in INITIAL_PROBLEMS}
    
    problems_chart = create_problems_chart(reports_this_year,PROBLEMS_TRANSLATION)
    session_chart = create_monthly_session_chart(sessions_this_year,MONTHS,SESSION_TYPES_TRANSLATION)

    sessions = create_sessions_by_month_dict(sessions_this_year,MONTHS)

    context = {
        'userGroups': request.user.groups.all(),
        'problemsChart':problems_chart,
        'sessionsChart':session_chart,
        'currentYear':year,
        'maxYear':datetime.now(timezone.utc).year,
        'states':Session.SESSION_STATES,
        'sessions':sessions,
        'months':MONTHS
    }

    return render(request,'sessions/list.html',context)


def create_problems_chart(reports,problems_translation):
    if not reports.exists():
        return '<span>No hay datos suficientes</span>'

    common_problems = reports.values('initial_problem').annotate(count=Count('initial_problem')).order_by('-count')[:10]

    problems_fig = px.pie(
        values=[report['count'] for report in common_problems],
        names=[problems_translation[report['initial_problem']] for report in common_problems],
        labels=[problems_translation[report['initial_problem']] for report in common_problems],
        color_discrete_sequence=['#ffb800','#402d7a','#ff0000','#00aabb','#d1ffac','#fface8','#acfff5','#fff7ac'],
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


def create_monthly_session_chart(sessions,months,session_types_translation):
    if not sessions.exists():
        return '<span>No hay datos suficientes</span>'

    x = []
    y = []
    color = []
    for month,month_name in months.items():
        for session_type,session_type_name in session_types_translation.items():
            sessions_month = sessions.filter(datetime__month=month,session_type=session_type)
            x.append(month_name)
            if sessions_month.exists():
                y.append(sessions_month.count())
                color.append(session_type_name)
            else:
                y.append(0)
                color.append('')

    sessions_fig = px.bar(
        x=x,
        y=y,
        color=color,
        labels={'x': 'Mes', 'y': 'Sesiones', 'color': 'Tipo'},
        color_discrete_sequence=['#ffb800','#402d7a','#ff0000']
    )
    sessions_fig.update_traces(
        hoverinfo='y',
        hovertemplate='Cantidad: %{y}',
        hoverlabel={
            'font':{
                'family':'OpenSans',
                'color':'#ffffff'},
            'bordercolor':'#000000'
        },
        textfont={
            'color':'#ffffff',
            'family':'OpenSans'
        })
    
    sessions_fig.update_layout(
        legend={
            'font':{'family':'OpenSans'}
        },
        font={
            'family':'Montserrat'
        },
        xaxis={
            'tickangle':-45,
            'categoryorder':'array',
            'categoryarray':[month for _,month in months.items()]
        },
    )

    return sessions_fig.to_html()


@require_http_methods(["POST"])
@group_required("technics")
def filter_session_list(request):
    MONTHS = {
        1:'Enero',
        2:'Febrero',
        3:'Marzo',
        4:'Abril',
        5:'Mayo',
        6:'Junio',
        7:'Julio',
        8:'Agosto',
        9:'Septiembre',
        10:'Octubre',
        11:'Noviembre',
        12:'Diciembre',
    }
    SESSION_TYPES_TRANSLATION = {t:text for t,text in Session.SESSION_TYPES}


    year = request.POST.get('year')
    session_list = Session.objects.filter(datetime__year=year)
    
    state = request.POST.get('state')
    if state:
        session_list = session_list.filter(session_state=state)
    
    technic_name = request.POST.get('technicName')
    if technic_name:
        session_list = session_list.filter(Q(technic__person__name__icontains=technic_name) | Q(technic__person__last_name__icontains=technic_name))
    
    patient_name = request.POST.get('patientName')
    if patient_name:
        session_list = session_list.filter(Q(patient__person__name__icontains=patient_name) | Q(patient__person__last_name__icontains=patient_name)).distinct()

    monthly_session_chart = create_monthly_session_chart(session_list,MONTHS,SESSION_TYPES_TRANSLATION)
    sessions_by_month = create_sessions_by_month_dict(session_list,MONTHS,True)

    return JsonResponse({
        'sessions':sessions_by_month,
        'sessionsChart':monthly_session_chart
    })


def create_sessions_by_month_dict(sessions,months,json_friendly=False):
    sessions_by_month = {}
    for m,month in months.items():
        these_sessions = sessions.filter(datetime__month=m).order_by('datetime')
        if these_sessions.exists():
            if json_friendly:
                sessions_this_month = []
                for session in these_sessions:
                    this_session_values = {
                        'datetime_day':session.datetime.strftime('%Y'),
                        'datetime_hour':session.datetime.strftime('%H:%M'),
                        'title':session.title,
                        'is_initial':session.is_initial,
                        'technic_full_name':str(session.technic.get_person()),
                        'patients':session.get_patients(),
                        'session_type':session.get_session_type_display(),
                        'session_state':session.get_session_state_display()
                    } 
                    sessions_this_month.append(this_session_values)
                sessions_by_month[month] = sessions_this_month
            else:
                sessions_by_month[month] = these_sessions

        else:
            sessions_by_month[month] = []
    return sessions_by_month
