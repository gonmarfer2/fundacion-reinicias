from django.db import models
from main.models import Patient
import re

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
    end_date = models.DateTimeField(null=True,verbose_name='Fecha de fin')
    state = models.CharField(max_length=1,choices=RECORD_STATES)
    initial_problem = models.CharField(max_length=3,choices=INITIAL_PROBLEMS,verbose_name='Demanda inicial')
    record = models.ForeignKey(PatientRecord,on_delete=models.CASCADE,verbose_name='Expediente')

    def __str__(self) -> str:
        return str(f'{self.initial_problem}: {self.start_date}-{self.end_date}')


class PatientRecordDocument(models.Model):
    document = models.FileField(upload_to='patientrecord/%Y/%m/%d',verbose_name='Documento de expediente')
    record = models.ForeignKey(PatientRecord,on_delete=models.CASCADE,verbose_name='Expediente')

    def __str__(self) -> str:
        full_name = self.resource.name
        filter_route = re.sub('patientrecord/\d+/\d+/\d+/','',full_name)
        filter_extension = re.sub('\.\w+','',filter_route)
        return filter_extension