from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_course,name='course_list'),
    path('register/', views.register_student,name='register_student'),
    path('<int:course_id>/inscribe', views.inscribe_in_course,name='inscribe')
]