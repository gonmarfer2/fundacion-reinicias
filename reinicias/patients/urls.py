from django.urls import path
from . import views

urlpatterns = [
    path('diary/<int:person_id>/',views.show_diary,name='patients_show_diary'),
    path('diary/<int:person_id>/create/',views.create_diary_entry,name='patients_create_diary_entry'),
    path('feelings/<int:person_id>/',views.show_feelings,name='patients_show_feelings'),
    path('<int:person_id>/tasks/',views.show_tasks_list,name='patients_show_tasks'),
    path('<int:person_id>/tasks/add/',views.add_tasks,name='patients_add_tasks'),
    path('<int:person_id>/tasks/<int:task_id>/',views.show_tasks_details,name='patients_detail_tasks'),
    path('<int:person_id>/tasks/<int:task_id>/delivery/',views.show_delivery_details,name='patients_show_delivery'),
    path('<int:person_id>/tasks/<int:task_id>/evaluate/',views.evaluate_task,name='patients_evaluate_task'),
    path('<int:person_id>/tasks/<int:task_id>/accept/',views.accept_task,name='patients_accept_task'),
    path('<int:person_id>/tasks/<int:task_id>/deny/',views.deny_task,name='patients_deny_task'),
]