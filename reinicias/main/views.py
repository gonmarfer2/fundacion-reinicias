from django.shortcuts import render,redirect
from django.views.decorators.http import require_http_methods
from django.core import serializers
from main.models import Group

@require_http_methods(["GET"])
def index(request):
    context = {
        'userGroups':serializers.serialize("json",request.user.groups.all()),
    }
    if request.user.groups.all().count() < 1:
        return render(request,'index.html',context)
    elif request.user.groups.filter(name="students").exists():
        return redirect('course_list')
    else:
        return render(request,'index_loggedin.html',context)
