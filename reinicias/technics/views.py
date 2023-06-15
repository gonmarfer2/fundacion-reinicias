from django.core.paginator import Paginator
from django.contrib.auth.models import Group
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from main.views import group_required
from main.models import Person, Teacher, Technic, GROUP_TRANSLATION_DICTIONARY 
from .models import PatientRecord, PatientRecordDocument, PatientRecordHistory, Patient
from django.http import Http404, JsonResponse
from .forms import MemberEditForm, PasswordChangeForm, MemberCreateForm
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q

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
    person_list = Person.objects.all()
    query_name = request.POST.get('query_name')
    if query_name:
        person_list = person_list.filter(Q(name__icontains=query_name) | Q(last_name__icontains=query_name))

    query_role = request.POST.get('query_role')
    if query_role:
        roles = Group.objects.filter(pk__in=query_role)
        person_list = person_list.filter(user__groups__in=roles)
    
    users = []
    for person in person_list.order_by('user__username'):
        users.append({
            'pk':person.pk,
            'username':person.user.username,
            'full_name':str(person),
            'groups':person.user.get_groups_display(),
            'email':person.user.email
        })
    print(users)
    return JsonResponse({
        'users':users
    })


@require_http_methods(["GET"])
@group_required("technics")
def show_session_list(request):
    year = request.GET.get('year')
