from django.core.paginator import Paginator
from django.contrib.auth.models import Group
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from main.views import group_required
from main.models import Person

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
