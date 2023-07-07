from django.db import models
import re
from datetime import datetime, timezone

FEELINGS = (
    ('ira','Ira'),
    ('agr','Agresividad'),
    ('fru','Frustración'),
    ('mie','Miedo'),
    ('hum','Humillación'),
    ('rec','Rechazo'),
    ('ans','Ansiedad'),
    ('ale','Alegría'),
    ('euf','Euforia'),
    ('res','Respeto'),
    ('sat','Satisfacción'),
    ('tri','Tristeza'),
    ('abu','Aburrimiento'),
    ('sol','Soledad'),
    ('dep','Depresión'),
    ('cul','Culpabilidad'),
    ('ign','Ignorancia'),
    ('ver','Vergüenza')
)

TASK_STATE = (
    ('w','En espera'),
    ('c','Completada'),
    ('a','Aceptada')
)


class Diary(models.Model):
    patient = models.OneToOneField('technics.patient',on_delete=models.CASCADE,verbose_name='Paciente')

    def __str__(self) -> str:
        return f'Diario de {self.patient}'
    
    class Meta:
        verbose_name_plural = 'Diarios'


class DiaryEntry(models.Model):

    datetime = models.DateTimeField(auto_now=True,verbose_name='Fecha y hora')
    title = models.CharField(max_length=255,verbose_name='Título')
    content = models.TextField(verbose_name='Contenido')
    feeling = models.CharField(max_length=3,verbose_name='Emoción',choices=FEELINGS)

    diary = models.ForeignKey(Diary,on_delete=models.CASCADE,verbose_name='Diario')
    
    def __str__(self) -> str:
        return self.title
    
    class Meta:
        verbose_name_plural = 'Entradas de diarios'


class Task(models.Model):
    title = models.CharField(max_length=255,verbose_name='Título')
    description = models.TextField(verbose_name='Descripción')
    state = models.CharField(max_length=1,verbose_name='Estado',choices=TASK_STATE)
    deadline = models.DateField(verbose_name='Fecha de entrega')
    feeling = models.CharField(max_length=3,verbose_name='Emoción',choices=FEELINGS,blank=True)

    patient = models.ForeignKey('technics.patient',on_delete=models.CASCADE,verbose_name='Paciente')
    technic = models.ForeignKey('main.technic',on_delete=models.CASCADE,verbose_name='Técnico')

    def __str__(self) -> str:
        return self.title
    
    def is_deadline_surpassed(self):
        return datetime.now(timezone.utc).date() > self.deadline
    
    class Meta:
        verbose_name_plural = 'Tareas'


class Delivery(models.Model):
    text = models.TextField(verbose_name='Entrega de texto')
    datetime = models.DateTimeField(auto_now=True,verbose_name='Fecha de entrega')

    patient = models.ForeignKey('technics.patient',on_delete=models.CASCADE,verbose_name='Paciente')
    task = models.ForeignKey(Task,on_delete=models.CASCADE,verbose_name='Tarea')

    def __str__(self) -> str:
        all_deliveries = list(Delivery.objects.filter(task=self.task).order_by('datetime'))
        this_order = all_deliveries.index(self)
        return f'Entrega {this_order} para la tarea {self.task}'
    
    class Meta:
        verbose_name_plural = 'Entregas de tareas'


class DeliveryDocument(models.Model):
    document = models.FileField(upload_to='deliveries/%Y/%m/%d',verbose_name='Documento de entrega')

    delivery = models.ForeignKey(Delivery,on_delete=models.CASCADE,verbose_name='Entrega')

    def __str__(self) -> str:
        full_name = self.document.name
        filter_route = re.sub('deliveries/\d+/\d+/\d+/','',full_name)
        filter_extension = re.sub('\.\w+','',filter_route)
        return filter_extension
    
    class Meta:
        verbose_name_plural = 'Documentos de entrega'