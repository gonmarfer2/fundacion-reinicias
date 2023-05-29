from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_course,name='course_list'),
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
] 