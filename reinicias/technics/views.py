from django.core.paginator import Paginator
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from main.views import group_required
from main.models import Person, Teacher, Technic, GROUP_TRANSLATION_DICTIONARY 
from .models import PatientRecord, PatientRecordDocument, PatientRecordHistory, Patient, Session, SessionNote, \
    InitialReport, INITIAL_PROBLEMS
from django.http import Http404, JsonResponse, FileResponse, HttpResponse
from .forms import MemberEditForm, PasswordChangeForm, MemberCreateForm, SessionCreateForm, SessionEditForm, \
    NoteCreateForm, InitialReportCreateForm, PatientCreateForm
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q, Count
import plotly.express as px
from datetime import datetime, timezone
from patients.models import Diary
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Flowable
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet
from django.templatetags.static import static
import io

# Constants
ERROR_404_PERSON = 'Ese usuario no existe'
ERROR_404_SESSION = 'Esa sesión no existe'
ERROR_404_SESSION_NOTE = 'Esa anotación no existe'
ERROR_404_REPORT = 'Ese informe no existe'

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
    if Person.objects.filter(pk=user_id).count() == 0:
        raise Http404(ERROR_404_PERSON)
    
    this_person = Person.objects.get(pk=user_id)
    if request.user.has_group('patients') and not request.user.has_group('technics') and this_person.pk != request.user.get_person().pk:
            raise PermissionDenied

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
    if Person.objects.filter(pk=user_id).count() == 0:
        raise Http404(ERROR_404_PERSON)
    
    this_person = Person.objects.get(pk=user_id)

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

            return redirect(f'/technics/users/{this_person.get_person().pk}/')

    context = {
        'thisUser':this_person,
        'form':form,
        'userGroups':request.user.groups.all()
    }

    return render(request,'users/register.html',context)


@require_http_methods(["GET","POST"])
def change_password(request,user_id):
    if Person.objects.filter(pk=user_id).count() == 0:
        raise Http404(ERROR_404_PERSON)
    this_person = Person.objects.get(pk=user_id)
    if this_person.get_user() != request.user and not request.user.is_superuser:
        raise PermissionDenied()
    
    form = PasswordChangeForm()

    if request.method == "POST":
        form = PasswordChangeForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            this_person.get_user().set_password(data.get('password1'))
            this_person.get_user().save()

            return redirect(f'/technics/users/{this_person.get_person().pk}/')
        
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

            return redirect(f'/technics/users/{new_person.pk}/')
    
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
                        'pk':session.pk,
                        'datetime_day':session.datetime.strftime('%d'),
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


@require_http_methods(["GET","POST"])
@group_required("technics")
@transaction.atomic()
def create_session(request):
    form = SessionCreateForm()

    if request.method == 'POST':
        form = SessionCreateForm(request.POST)

        if form.is_valid():
            data = form.cleaned_data
            session = form.save(commit=False)
            session_datetime = datetime.strptime(f'{data.get("date")} {data.get("time")}','%Y-%m-%d %H:%M:%S')
            session.datetime = session_datetime
            session.session_state='p'
            session.save()
            session.patient.set(data.get('patient'))
            return redirect(f'/technics/sessions/{session.pk}/')

    context = {
        'userGroups':request.user.groups.all(),
        'form':form
    }
    return render(request,'sessions/create.html',context)


@require_http_methods(["GET"])
@group_required("technics")
@transaction.atomic()
def delete_session(request,session_id):
    if Session.objects.filter(pk=session_id).count() == 0:
        raise Http404(ERROR_404_SESSION)
    
    Session.objects.get(pk=session_id).delete()

    return JsonResponse({'response':'ok'})


@require_http_methods(["GET","POST"])
@group_required("technics")
@transaction.atomic()
def edit_session(request,session_id):
    if Session.objects.filter(pk=session_id).count() == 0:
        raise Http404(ERROR_404_SESSION)
    
    this_session = Session.objects.get(pk=session_id)
    initial = {
        'date':this_session.datetime.strftime('%Y-%m-%d'),
        'time':this_session.datetime.time()
    }

    form = SessionEditForm(instance=this_session,initial=initial,request=request)

    if request.method == 'POST':
        form = SessionEditForm(request.POST,instance=this_session,request=request)

        if form.is_valid():
            data = form.cleaned_data
            this_session_datetime = datetime.strptime(f'{data.get("date")} {data.get("time")}','%Y-%m-%d %H:%M:%S')
            this_session.datetime = this_session_datetime
            this_session.title = data.get('title')
            this_session.is_initial = data.get('is_initial')
            this_session.session_type = data.get('session_type')
            this_session.session_state = data.get('session_state')
            this_session.technic = data.get('technic')
            this_session.patient.set(data.get('patient'))
            this_session.save()
            return redirect(f'/technics/sessions/{this_session.pk}/')

    context = {
        'userGroups':request.user.groups.all(),
        'form':form
    }
    return render(request,'sessions/edit.html',context)


@require_http_methods(["GET"])
@group_required("technics")
def show_session_details(request,session_id):
    if Session.objects.filter(pk=session_id).count() == 0:
        raise Http404(ERROR_404_SESSION)
    
    this_session = Session.objects.get(pk=session_id)
    initial = {
        'date':this_session.datetime.strftime('%Y-%m-%d'),
        'time':this_session.datetime.time()
    }

    form = SessionEditForm(instance=this_session,initial=initial,disabled=True)

    notes = SessionNote.objects.filter(session=this_session).order_by('-creation_datetime')

    report = InitialReport.objects.filter(session=this_session).first()

    context = {
        'userGroups':request.user.groups.all(),
        'form':form,
        'session':this_session,
        'notes':notes,
        'report':report
    }
    return render(request,'sessions/details.html',context)


@require_http_methods(["GET","POST"])
@group_required("technics")
@transaction.atomic()
def add_note_session(request,session_id):
    if Session.objects.filter(pk=session_id).count() == 0:
        raise Http404(ERROR_404_SESSION)
    
    this_session = Session.objects.get(pk=session_id)
    form = NoteCreateForm()

    if request.method == 'POST':
        form = NoteCreateForm(request.POST)

        if form.is_valid():
            new_note = form.save(commit=False)

            this_technic = Technic.objects.get(person__user=request.user)
            new_note.technic = this_technic
            new_note.session = this_session
            new_note.save()

            return redirect(f'/technics/sessions/{this_session.pk}')

    context = {
        'session':this_session,
        'userGroups':request.user.groups.all(),
        'form':form
    }
    return render(request, 'sessions/notes/create.html', context)


@require_http_methods(["GET"])
@group_required("technics")
@transaction.atomic()
def delete_note_session(request,session_id,note_id):
    if SessionNote.objects.filter(pk=note_id).count() == 0:
        raise Http404(ERROR_404_SESSION_NOTE)
    
    SessionNote.objects.get(pk=note_id).delete()

    return JsonResponse({'response':'ok'})


@require_http_methods(["GET","POST"])
@group_required("technics")
@transaction.atomic()
def create_report_session(request,session_id):
    if Session.objects.filter(pk=session_id).count() == 0:
        raise Http404(ERROR_404_SESSION)
    
    this_session = Session.objects.get(pk=session_id)
    form = InitialReportCreateForm(session_id=this_session.pk)

    if request.method == 'POST':
        form = InitialReportCreateForm(request.POST,session_id=this_session.pk)

        if form.is_valid():
            new_report = form.save(commit=False)
            new_report.session = this_session
            new_report.save()

            return redirect(f'/technics/sessions/{this_session.pk}/reports/{new_report.pk}/')
    
    context = {
        'userGroups':request.user.groups.all(),
        'form':form,
        'submitText':'Crear'
    }

    return render(request,'sessions/reports/create.html',context)


@require_http_methods(["GET"])
@group_required("technics")
@transaction.atomic()
def show_report_session(request,session_id,report_id):
    if InitialReport.objects.filter(pk=report_id).count() == 0:
        raise Http404(ERROR_404_REPORT)
    
    this_report = InitialReport.objects.get(pk=report_id)
    form = InitialReportCreateForm(instance=this_report,disabled=True)
    record_exists = PatientRecord.objects.filter(number=this_report.record_number)

    context = {
        'userGroups':request.user.groups.all(),
        'form':form,
        'hasRecord':record_exists
    }

    return render(request,'sessions/reports/details.html',context)


@require_http_methods(["GET","POST"])
@group_required("technics")
@transaction.atomic()
def edit_report_session(request,session_id,report_id):
    if Session.objects.filter(pk=session_id).count() == 0:
        raise Http404(ERROR_404_SESSION)
    if InitialReport.objects.filter(pk=report_id).count() == 0:
        raise Http404(ERROR_404_REPORT)
    
    this_session = Session.objects.get(pk=session_id)
    this_report = InitialReport.objects.get(pk=report_id)
    form = InitialReportCreateForm(instance=this_report,session_id=this_session.pk)

    if request.method == 'POST':
        form = InitialReportCreateForm(request.POST,instance=this_report,session_id=this_session.pk)

        if form.is_valid():
            form.save()

            return redirect(f'/technics/sessions/{this_session.pk}/reports/{this_report.pk}/')
    
    context = {
        'userGroups':request.user.groups.all(),
        'form':form,
        'submitText':'Aceptar cambios'
    }

    return render(request,'sessions/reports/create.html',context)


@require_http_methods(["GET","POST"])
@group_required("technics")
@transaction.atomic()
def register_patient_report(request,session_id,report_id):
    if Session.objects.filter(pk=session_id).count() == 0:
        raise Http404(ERROR_404_SESSION)
    if InitialReport.objects.filter(pk=report_id).count() == 0:
        raise Http404(ERROR_404_REPORT)
    
    this_report = InitialReport.objects.get(pk=report_id)

    initial_values = {
        'name':this_report.name,
        'last_name':this_report.last_name,
        'roles':'Paciente'
    }
    form = PatientCreateForm(initial=initial_values)
    print(form.data)

    if request.method == 'POST':
        form = PatientCreateForm(request.POST,initial=initial_values)

        if form.is_valid():
            new_user = form.save(commit=False)
            new_user.save()

            data = form.cleaned_data
            
            new_user.groups.add(Group.objects.get_or_create(name='patients')[0])

            new_person = Person(
                user=new_user,
                name=this_report.name,
                last_name=this_report.last_name,
                birth_date=data.get('birth_date'),
                telephone=data.get('telephone'),
                sex=data.get('sex')
                )
            new_person.save()

            new_patient = Patient(
                person=new_person,
                school=data.get('school')
            )
            new_patient.save()

            new_patient_record = PatientRecord(
                number=this_report.record_number,
                patient=new_patient
            )
            new_patient_record.save()

            new_patient_record_history_entry = PatientRecordHistory(
                state='a',
                initial_problem=this_report.initial_problem,
                record=new_patient_record
            )
            new_patient_record_history_entry.save()

            new_diary = Diary(
                patient=new_patient
            )
            new_diary.save()

            return redirect(f'/technics/users/{new_person.pk}')

    
    context = {
        'userGroups':request.user.groups.all(),
        'form':form,
        'submitText':'Registrar'
    }

    return render(request,'sessions/reports/register_patient.html',context)


@require_http_methods(["GET"])
@group_required("technics")
def report_generate_pdf(request,session_id,report_id):
    if Session.objects.filter(pk=session_id).count() == 0:
        raise Http404(ERROR_404_SESSION)
    if InitialReport.objects.filter(pk=report_id).count() == 0:
        raise Http404(ERROR_404_REPORT)
    
    this_report = InitialReport.objects.get(pk=report_id)

    class DocHeader(Flowable):
        def __init__(self,date,record_number,img_data):
            super().__init__()
            self.date = date.strftime("%d/%m/%Y %H:%M")
            self.record_number = record_number
            self.img = ImageReader(img_data)

        def draw(self):
            self.canv.drawImage(self.img, 10*cm, -cm-10, height=2*cm, width=6*cm, mask='auto')
            text_header = self.canv.beginText(0,0)
            text_header.setFont('Helvetica-Bold',24)
            text_header.textLine('INFORME SOCIAL')
            text_header.setFont('Helvetica-Bold',12)
            text_header.textLine(f'FECHA: {self.date}')
            text_header.textLine(f'Nº EXPEDIENTE: {self.record_number}')
            self.canv.drawText(text_header)

    doc_buffer = io.BytesIO()
    pdf_report_attrs = {
        'initial_problem':'Demanda inicial',
        'treatment_type':'Tipo de tratamiento',
        'first_evaluation':'Primera evaluación / presunción diagnóstica',
        'family_situation':'Situación familiar / antecedentes familiares',
        'social_situation':'Situación social: relaciones sociales y con el entorno',
        'academic_situation':'Situación académica y evolución escolar',
        'problem_situation':'Situación-problema',
        'drug_history':'Historia de consumo de drogas: edad de inicio, patrón, evolución',
        'leisure':'Ocio y ocupación del tiempo libre',
        'labour_situation':'Situación laboral / Situación económica de la familia',
        'social_diagnostic':'Diagnóstico social',
        'answer_plan':'Plan de actuación',
        'observations':'Observaciones: pautas de conducta con las que se comporta',
        }

    styles = getSampleStyleSheet()
    STYLE_N = styles['Normal']
    STYLE_H = styles['Heading1']

    story = []

    logo_url = request.build_absolute_uri(static('assets/fundacionReiniciasLogo.png'))
    header = DocHeader(this_report.datetime,this_report.record_number,logo_url)
    story.append(header)
    # story.append(Image(logo_url,width=6*cm,height=2*cm,hAlign='RIGHT',useDPI=True))
    story.append(Spacer(0,2*cm))

    story.append(Paragraph('Nombre y apellidos',STYLE_H))
    story.append(Paragraph(f'{this_report.name} {this_report.last_name}',STYLE_N))
    story.append(Spacer(0,cm))

    for attr in pdf_report_attrs:
        story.append(Paragraph(str(pdf_report_attrs[attr]),STYLE_H))
        if attr == 'initial_problem':
            story.append(Paragraph(this_report.get_initial_problem_display(),STYLE_N))
        else:
            story.append(Paragraph(str(getattr(this_report,attr)),STYLE_N))
        story.append(Spacer(0,cm))

    doc = SimpleDocTemplate(doc_buffer,pagesize=A4)
    doc.build(story)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename={this_report}.pdf'
    response.write(doc_buffer.getvalue())
    doc_buffer.close()

    return response
