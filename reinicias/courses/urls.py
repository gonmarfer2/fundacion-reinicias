from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_course,name='course_list'),
    path('register/', views.register_student,name='register_student')
]