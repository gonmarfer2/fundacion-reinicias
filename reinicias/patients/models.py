from django.db import models

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


class Diary(models.Model):
    patient = models.OneToOneField("technics.patient",on_delete=models.CASCADE,verbose_name='Paciente')

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
