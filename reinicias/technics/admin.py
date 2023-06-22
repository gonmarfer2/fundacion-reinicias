from django.contrib import admin
from .models import PatientRecord,PatientRecordDocument,PatientRecordHistory,Patient,Session,SessionNote,InitialReport

admin.site.register(PatientRecord)
admin.site.register(PatientRecordDocument)
admin.site.register(PatientRecordHistory)
admin.site.register(Patient)
admin.site.register(Session)
admin.site.register(SessionNote)
admin.site.register(InitialReport)