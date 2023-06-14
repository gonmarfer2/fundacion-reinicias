from django.contrib import admin
from .models import PatientRecord,PatientRecordDocument,PatientRecordHistory

admin.site.register(PatientRecord)
admin.site.register(PatientRecordDocument)
admin.site.register(PatientRecordHistory)