from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render,redirect
from django.views.decorators.http import require_http_methods

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
