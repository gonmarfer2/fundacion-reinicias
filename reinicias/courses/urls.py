from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_course,name='course_list'),
    path('filter/students/',views.filter_courses_students,name='filter_students'),
    path('create/', views.create_course,name='create_course'),
    path('register/', views.register_student,name='register_student'),
    path('<int:course_id>/edit',views.edit_course,name='course_edit'),
    path('<int:course_id>/delete',views.delete_course,name='course_delete'),
    path('<int:course_id>/inscribe', views.inscribe_in_course,name='inscribe'),
    path('<int:course_id>/unpublish', views.unpublish_course,name='unpublish_course'),
    path('<int:course_id>/units/create/',views.create_unit,name='create_unit'),
    path('<int:course_id>/units/<int:unit_id>/edit/',views.edit_unit,name='edit_unit'),
    path('<int:course_id>/units/<int:unit_id>/delete/',views.delete_unit,name='delete_unit'),
    path('<int:course_id>/units/<int:unit_id>/resources/add/',views.add_unit_resources,name='add_unit_resources'),
    path('<int:course_id>/units/<int:unit_id>/resources/<int:resource_id>/remove',views.remove_unit_resources,name='remove_unit_resources'),
    path('<int:course_id>/',views.details_course,name='course_details'),
    path('<int:course_id>/students',views.list_course_students,name='course_students'),
    path('autoevaluations/<int:autoevaluation_id>/',views.autoevaluation_view,name='autoevaluation_show'),
    path('autoevaluations/<int:autoevaluation_id>/edit/',views.autoevaluation_edit,name='autoevaluation_edit'),
    path('autoevaluations/<int:autoevaluation_id>/questions/add/',views.autoevaluation_add_question,name='autoevaluation_add_question'),
    path('autoevaluations/<int:autoevaluation_id>/questions/<int:question_id>/delete/',views.autoevaluation_delete_question,name='autoevaluation_delete_question'),
    path('autoevaluations/<int:autoevaluation_id>/questions/<int:question_id>/edit/',views.autoevaluation_edit_question,name='autoevaluation_edit_question'),
    path('options/<int:question_option>/delete/',views.remove_question_option,name='question_remove_option'),
    path('questions/<int:question_id>/options/add/',views.add_question_option,name='question_add_option'),
    path('autoevaluations/<int:autoevaluation_id>/start/',views.autoevaluation_start,name='autoevaluation_start'),
    path('autoevaluations/<int:autoevaluation_id>/process/',views.autoevaluation_process,name='process_autoevaluation')
] 