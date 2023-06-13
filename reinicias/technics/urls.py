from django.urls import path
from . import views

urlpatterns = [
    path('users/',views.show_user_list,name='technics_user_list'),
    path('users/<int:user_id>/',views.show_user_details,name='technics_user_details'),
    path('users/<int:user_id>/edit/',views.edit_user,name="technics_edit_user")
]