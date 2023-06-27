from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render,redirect
from django.views.decorators.http import require_http_methods
from .models import Notification, User
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.core.paginator import Paginator

@require_http_methods(["GET"])
def index(request):
    context = {
        'userGroups':request.user.groups.all(),
    }
    if request.user.groups.all().count() < 1:
        return render(request,'index.html',context)
    elif request.user.groups.filter(name="students").exists():
        return redirect('course_list')
    else:
        return render(request,'index_loggedin.html',context)


# CUSTOM DECORATOR
def group_required(*group_names):
    def has_group(user):
        if user.is_authenticated:
            if user.groups.filter(name__in=set(group_names)).exists() or user.is_superuser:
                return True
        return False
    return user_passes_test(has_group, login_url='login')


@require_http_methods(["GET"])
def check_new_notifications(request):
    notifications = Notification.objects.filter(user=request.user,read_date__isnull=True)
    return JsonResponse({'new':notifications.exists()})


@login_required(login_url='login')
@require_http_methods(["GET"])
def show_notifications(request):
    unread_notifications = Notification.objects.filter(user=request.user,read_date__isnull=True)
    read_notifications = Notification.objects.filter(user=request.user,read_date__isnull=False)

    page_number = request.GET.get('page',None)    
    paginator_read = Paginator(read_notifications,5)
    page_obj = paginator_read.get_page(page_number)

    context = {
        'userGroups':request.user.groups.all(),
        'readNotifications':page_obj,
        'unreadNotifications':unread_notifications,
        'pages': {
            'current':int(page_obj.number),
            'has_previous':page_obj.has_previous(),
            'has_next':page_obj.has_next()
        }
    }

    return render(request,'notifications/show.html',context)


@login_required(login_url='login')
@require_http_methods(["POST"])
def update_read_notifications(request):
    user_id = request.POST.get('user_id')
    this_user = User.objects.get(pk=user_id)
    Notification.objects.filter(user=this_user,read_date__isnull=True).update(read_date=timezone.now())

    return JsonResponse({'response':'ok'})
