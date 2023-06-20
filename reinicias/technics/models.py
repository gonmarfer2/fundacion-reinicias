from django.db import models
import re
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

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

class Patient(models.Model):
    person = models.OneToOneField("main.Person",on_delete=models.CASCADE, verbose_name="Usuario")
    school = models.CharField(max_length=255,verbose_name='Centro Educativo')

    def __str__(self) -> str:
        return str(self.person)
    
    def get_user(self):
        return self.person.user
    
    def get_person(self):
        return self.person

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

    start_date = models.DateTimeField(auto_now_add=True,verbose_name='Fecha de inicio')
    end_date = models.DateTimeField(blank=True,null=True,verbose_name='Fecha de fin')
    state = models.CharField(max_length=1,choices=RECORD_STATES)
    initial_problem = models.CharField(blank=True,null=True,max_length=3,choices=INITIAL_PROBLEMS,verbose_name='Demanda inicial')
    record = models.ForeignKey(PatientRecord,on_delete=models.CASCADE,verbose_name='Expediente')

    def __str__(self) -> str:
        return str(f'{self.initial_problem if self.initial_problem else "-"}: {self.record} - {self.start_date}')
    
    def save(self,recursive=True,*args,**kwargs) -> None:
        previous = PatientRecordHistory.objects.filter(record=self.record).order_by('-start_date')
        super().save()
        if previous.exists():
            previous = previous.first()
            if recursive:
                previous.end_date = self.start_date
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
    

class Session(models.Model):
    SESSION_TYPES = (
        ('i','Individual'),
        ('f','Familiar'),
        ('g','Grupal')
    )
    SESSION_STATES = (
        ('p','Pendiente'),
        ('f','Falta'),
        ('a','Anulada'),
        ('c','Completada')
    )
    datetime = models.DateTimeField(verbose_name='Fecha y hora')
    title = models.CharField(max_length=1024,verbose_name='Título')
    is_initial = models.BooleanField(verbose_name='Inicial')
    session_type = models.CharField(max_length=1,choices=SESSION_TYPES,verbose_name='Tipo de sesión')
    session_state = models.CharField(max_length=1,choices=SESSION_STATES,verbose_name='Estado de la sesión')

    patient = models.ManyToManyField(Patient,blank=True,verbose_name='Pacientes')
    technic = models.ForeignKey('main.Technic',on_delete=models.CASCADE  ,verbose_name='Técnico')

    def __str__(self) -> str:
        return self.title

    def has_patients(self):
        return self.patient is not None and self.patient.exists()
    
    def get_patients(self):
        patient_names = []
        for patient in self.patient.all():
            patient_names.append(str(patient.get_person()))
        res = ", ".join(list(patient_names)) if len(patient_names) > 0 else "-"
        return res

class SessionNote(models.Model):
    text = models.TextField(verbose_name='Texto')
    creation_datetime = models.DateTimeField(verbose_name='Fecha y hora de creación',auto_now=True)

    technic = models.ForeignKey('main.Technic',on_delete=models.CASCADE,verbose_name='Técnico')
    session = models.ForeignKey(Session,on_delete=models.CASCADE,verbose_name='Sesión')

    def __str__(self) -> str:
        return self.text


class InitialReport(models.Model):
    datetime =models.DateTimeField(verbose_name='Fecha y hora')
    record_number = models.CharField(max_length=255,validators=[
        RegexValidator(regex=r"^FR1800\d+",
                       message="El expediente debe tener el formato FR1800X, donde X es una cifra entera positiva.")
        ],verbose_name="Número de expediente")
    initial_problem = models.CharField(max_length=3,choices=INITIAL_PROBLEMS,verbose_name='Tipo de demanda')
    name = models.CharField(max_length=255,verbose_name='Nombre')
    last_name = models.CharField(max_length=255,verbose_name='Apellidos')
    treatment_type = models.TextField(verbose_name='Tipo de tratamiento')
    first_evaluation = models.TextField(verbose_name='Primera evaluación')
    family_situation = models.TextField(verbose_name='Situación familiar / Antecedentes familiares')
    social_situation = models.TextField(verbose_name='Situación social')
    academic_situation = models.TextField(verbose_name='Situación académica y evolución escolar')
    problem_situation = models.TextField(verbose_name='Situación-problema')
    drug_history = models.TextField(verbose_name='Historial de consumo de drogas')
    leisure = models.TextField(verbose_name='Ocio y ocupación del tiempo libre')
    labour_situation = models.TextField(verbose_name='Situación laboral/económica de la familia')
    social_diagnostic = models.TextField(verbose_name='Diagnóstico social')
    answer_plan = models.TextField(verbose_name='Plan de actuación')
    observations = models.TextField(verbose_name='Observaciones')

    session = models.ForeignKey(Session,on_delete=models.CASCADE,verbose_name='Sesión')

    def __str__(self) -> str:
        return f'Informe inicial {self.record_number}'
