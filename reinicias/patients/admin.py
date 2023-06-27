from django.contrib import admin
from .models import Diary, DiaryEntry, Task, Delivery, DeliveryDocument

admin.site.register(DiaryEntry)
admin.site.register(Diary)
admin.site.register(Task)
admin.site.register(Delivery)
admin.site.register(DeliveryDocument)
