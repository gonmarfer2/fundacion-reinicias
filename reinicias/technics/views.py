from django.core.paginator import Paginator
from django.contrib.auth.models import Group
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from main.views import group_required
from main.models import Person
from .models import Patient
from django.http import Http404

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
    if this_person.user.groups.filter(name='patients').exists():
        this_person = Patient.objects.get(person=this_person)

    context = {
        'thisUser': this_person,
        'userGroups':request.user.groups.all()
    }

    return render(request,'users/details.html',context)