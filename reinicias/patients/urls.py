from django.urls import path
from . import views

urlpatterns = [
    path('diary/<int:person_id>/',views.show_diary,name='patients_show_diary'),
    path('diary/<int:person_id>/create/',views.create_diary_entry,name='patients_create_diary_entry')
]