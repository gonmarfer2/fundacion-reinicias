from django.contrib import admin
from .models import Diary, DiaryEntry

admin.site.register(DiaryEntry)
admin.site.register(Diary)
