from typing import Iterable, Optional
from django.db import models
from main.models import Patient
import re
from django.core.exceptions import ValidationError

class PatientRecord(models.Model):

    number = models.CharField(max_length=255,verbose_name='Número de expediente')
    patient = models.OneToOneField(Patient,null=True,on_delete=models.SET_NULL,verbose_name='Paciente')

    def __str__(self) -> str:
        return str(self.number)
    

class PatientRecordHistory(models.Model):
    RECORD_STATES = (
        ('a','Activo'),
        ('l','Alta'),
        ('b','Baja'),
        ('d','Derivado')
    )

    INITIAL_PROBLEMS = (
        ('byc','Bullying y Ciberbullying'),
        ('adi','Adicciones'),
        ('emo','Dificultades emocionales'),
        ('fam','Conflictos familiares'),
        ('spe','Superación Personal'),
        ('cov','COVID-19'),
        ('soc','Dificultades sociales'),
        ('tox','Relaciones tóxicas'),
        ('pef','Punto de encuentro familiar'),
        ('epm','Escuela de Padres y Madres'),
        ('apj','Acompañamiento en procesos judiciales'),
        ('pps','Peritaje psicológico y social'),
        ('tmi','Tratamiento en maltrato infantil'),
        ('sap','Servicio de Atención al profesorado'),
        ('smf','Servicio de Mediación Familiar'),
        ('sof','Servicio de Orientación Familiar'),
    )

    start_date = models.DateTimeField(auto_now_add=True,verbose_name='Fecha de inicio')
    end_date = models.DateTimeField(blank=True,null=True,verbose_name='Fecha de fin')
    state = models.CharField(max_length=1,choices=RECORD_STATES)
    initial_problem = models.CharField(blank=True,max_length=3,choices=INITIAL_PROBLEMS,verbose_name='Demanda inicial')
    record = models.ForeignKey(PatientRecord,on_delete=models.CASCADE,verbose_name='Expediente')

    def __str__(self) -> str:
        return str(f'{self.initial_problem if self.initial_problem else "-"}: {self.start_date}-{self.end_date}')
    
    def save(self,recursive=True) -> None:
        previous = PatientRecordHistory.objects.filter(record=self.record).order_by('-start_date')
        if previous.exists():
            previous = previous.first()
        super().save()
        if recursive:
                previous.end_date = self.start_date
                print(self.start_date)
                print(previous.end_date)
                previous.save(recursive=False)

    def clean(self):
        if (self.state == 'a' and self.initial_problem is None) \
            or (self.state != 'a' and self.initial_problem is not None):
            raise ValidationError(
                'La demanda inicial solo se debe incluir si el estado es Activo, si no, no hay que ponerlo',
                code='technics_record_history_state_problem'
            )


class PatientRecordDocument(models.Model):
    document = models.FileField(upload_to='patientrecord/%Y/%m/%d',verbose_name='Documento de expediente')
    record = models.ForeignKey(PatientRecord,on_delete=models.CASCADE,verbose_name='Expediente')

    def __str__(self) -> str:
        full_name = self.document.name
        filter_route = re.sub('patientrecord/\d+/\d+/\d+/','',full_name)
        filter_extension = re.sub('\.\w+','',filter_route)
        return filter_extension