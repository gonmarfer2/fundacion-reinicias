from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('notifications/check/',views.check_new_notifications,name='check_new_notifications'),
    path('notifications/',views.show_notifications,name='notifications_show'),
    path('notifications/read/',views.update_read_notifications,name='notifications_read')
]