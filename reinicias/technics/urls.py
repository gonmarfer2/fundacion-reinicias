from django.urls import path
from . import views

urlpatterns = [
    path('users/',views.show_user_list,name='technics_user_list')
]