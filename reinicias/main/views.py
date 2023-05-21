from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.core import serializers

@require_http_methods(["GET"])
def index(request):
    context = {
        'userGroups':serializers.serialize("json",request.user.groups.all()),
    }
    if request.user.groups.all().count() < 1:
        return render(request,'index.html',context)
    else:
        return render(request,'index_loggedin.html',context)
