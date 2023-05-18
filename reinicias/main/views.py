from django.shortcuts import render
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET"])
def index(request):
    if request.user.groups.all().count() < 1:
        return render(request,'index.html')
    else:
        return render(request,'index_menu.html')
