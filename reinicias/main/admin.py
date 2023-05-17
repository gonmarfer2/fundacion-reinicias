from django.contrib import admin
from .models import User,Person,UserManager

admin.site.register(User)
# admin.site.register(Role)
admin.site.register(Person)