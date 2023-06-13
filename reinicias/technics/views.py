from django.core.paginator import Paginator
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from main.views import group_required
from main.models import Person,Patient
from .models import PatientRecord,PatientRecordDocument,PatientRecordHistory
from django.http import Http404
from .forms import MemberEditForm, PasswordChangeForm
from django.urls import reverse
from django.core.exceptions import PermissionDenied

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
        'roles':Group.objects.all(),
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
    
    this_person = Person.objects.get(user__pk=user_id)
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

            roles = Group.objects.filter(name__in=data.get('roles')) if type(data.get('roles')) == 'list' \
                else Group.objects.filter(name=data.get('roles'))
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