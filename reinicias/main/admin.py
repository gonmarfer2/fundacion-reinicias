from django.contrib import admin
from .models import User,Person,Teacher,Patient

admin.site.register(User)
admin.site.register(Person)
admin.site.register(Teacher)
admin.site.register(Patient)