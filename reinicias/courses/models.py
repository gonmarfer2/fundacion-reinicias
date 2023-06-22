from django.db import models
from main.models import Person, Teacher
from django.core.validators import MaxValueValidator, MinValueValidator
from datetime import datetime, timezone, timedelta
import re
from django.db.models import OuterRef, Exists
from django.db.models.functions import Coalesce
from django.db.models.expressions import Subquery

class Course(models.Model):
    # Existe el atributo error_messages para los campos que permite poner errores personalizados para claves por defecto
    name = models.CharField(max_length=256,blank=False,verbose_name="Nombre",unique=True)
    description = models.TextField(blank=False,verbose_name="Descripción")
    published = models.BooleanField(verbose_name="Publicado")
    duration = models.IntegerField(validators=[MinValueValidator(1)],verbose_name="Duración")
    teacher = models.ForeignKey(Teacher,on_delete=models.CASCADE,verbose_name="Formador")
    index_document = models.FileField(upload_to='course/%Y/%m/%d',null=True,verbose_name="Índice de curso")
    preceeded_by = models.ManyToManyField("self",blank=True,symmetrical=False,verbose_name="Predecesores")
    creation_date = models.DateTimeField(auto_now_add=True,verbose_name='Fecha de creación')

    DEFAULT_COURSE_DURATION = 30

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = "courses_course"

class CourseUnitResource(models.Model):
    resource = models.FileField(upload_to='courseunit/%Y/%m/%d',verbose_name="Recurso")
    course_unit = models.ForeignKey("CourseUnit",on_delete=models.CASCADE,verbose_name="Tema")

    def __str__(self) -> str:
        full_name = self.resource.name
        filter_route = re.sub('courseunit/\d+/\d+/\d+/','',full_name)
        filter_extension = re.sub('\.\w+','',filter_route)
        return filter_extension
    
    def get_file_with_extension(self) -> str:
        full_name = self.resource.name
        filter_route = re.sub('courseunit/\d+/\d+/\d+/','',full_name)
        return filter_route

class CourseUnit(models.Model):
    title = models.CharField(max_length=256,blank=False,verbose_name="Título")
    order = models.PositiveSmallIntegerField(verbose_name="Orden")
    course = models.ForeignKey(Course,on_delete=models.CASCADE,verbose_name="Curso")

    def __str__(self) -> str:
        return self.title
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['course','order'],
                name='order_in_course',
                deferrable=models.Deferrable.DEFERRED,
            ),
            models.UniqueConstraint(
                fields=['course','title'],
                name='title_in_course',
                deferrable=models.Deferrable.DEFERRED,
            )]

class Autoevaluation(models.Model):
    title = models.CharField(max_length=256,blank=False,verbose_name="Título")
    duration = models.PositiveIntegerField(verbose_name="Duración (minutos)")
    instructions = models.TextField(blank=False,verbose_name="Instrucciones")
    penalization_factor = models.FloatField(validators=[MinValueValidator(0.0),MaxValueValidator(1.0)],verbose_name="Factor de penalización")
    course_unit = models.OneToOneField(CourseUnit,on_delete=models.CASCADE,verbose_name="Tema")

    def __str__(self) -> str:
        return self.title

class Question(models.Model):
    question = models.TextField(blank=False,verbose_name="Pregunta")
    order = models.PositiveSmallIntegerField(verbose_name="Orden")
    is_multiple = models.BooleanField(verbose_name="Es de respuesta múltiple")
    autoevaluation = models.ForeignKey(Autoevaluation,on_delete=models.CASCADE,verbose_name="Autoevaluación")

    def __str__(self) -> str:
        return self.question
    
    def get_points(self):
        total_questions = Question.objects.filter(autoevaluation=self.autoevaluation).count()
        return 10/total_questions
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['autoevaluation','order'],
                name='order_in_autoevaluation',
                deferrable=models.Deferrable.DEFERRED,
            )
        ]
    
    @staticmethod
    def get_last_order(autoevaluation_id):
        last_question = Question.objects.filter(autoevaluation=autoevaluation_id).order_by('-order')
        if last_question.exists():
            return last_question.first().order
        else:
            return 0
        
    def insert_self(self,new_order):
        old_order = self.order
        if Question.objects.filter(autoevaluation=self.autoevaluation,order=new_order).exists():
            if new_order < old_order:
                Question.objects.filter(autoevaluation=self.autoevaluation,order__gte=new_order,order__lt=old_order).exclude(pk=self.pk).update(order=models.F('order')+1)
            elif new_order > old_order:
                Question.objects.filter(autoevaluation=self.autoevaluation,order__gt=new_order).exclude(pk=self.pk).update(order=models.F('order')+1)
                Question.objects.filter(autoevaluation=self.autoevaluation,order__gt=old_order,order__lte=new_order).exclude(pk=self.pk).update(order=models.F('order')-1)
        
        self.order = new_order


class QuestionOption(models.Model):
    option_name = models.CharField(max_length=256,verbose_name="Opción")
    is_correct = models.BooleanField(verbose_name="Es respuesta correcta")
    question = models.ForeignKey(Question,on_delete=models.CASCADE,verbose_name="Pregunta")

    def __str__(self) -> str:
        return self.option_name

class Student(models.Model):
    person = models.OneToOneField(Person,on_delete=models.CASCADE,verbose_name="Usuario")
    courses = models.ManyToManyField(Course,blank=True,through="CourseStatus",verbose_name="Cursos")
    autoevaluations = models.ManyToManyField(Autoevaluation,blank=True,through="Calification",verbose_name="Autoevaluaciones")
    options_chosen = models.ManyToManyField(QuestionOption,blank=True,verbose_name="Opciones escogidas")

    def __str__(self) -> str:
        return str(self.person)
    
    def get_user(self):
        return self.person.user
    
    def get_person(self):
        return self.person

class Calification(models.Model):
    calification = models.FloatField(null=True,validators=[MinValueValidator(0.0),MaxValueValidator(10.0)],verbose_name="Calificación")
    start_date = models.DateTimeField(verbose_name="Fecha de comienzo")
    end_date = models.DateTimeField(null=True,verbose_name="Fecha de finalización")
    student = models.ForeignKey(Student,on_delete=models.CASCADE,verbose_name="Estudiante")
    autoevaluation = models.ForeignKey(Autoevaluation,on_delete=models.CASCADE,verbose_name="Autoevaluación")

    def __str__(self) -> str:
        return str(self.calification)
    
    def get_value(self):
        value = 0.0
        questions = Question.objects.filter(autoevaluation=self.autoevaluation)
        questions_count = questions.count()
        for question in questions:
            students_answers = self.student.options_chosen.filter(question=question)
            if not question.is_multiple:
                for answer in students_answers:
                    value += self.__sum_value(answer,float(self.autoevaluation.penalization_factor),questions_count)
            else:
                question_options_count = QuestionOption.objects.filter(question=question).count()
                for answer in students_answers:
                    value += self.__sum_value(answer,float(self.autoevaluation.penalization_factor),(questions_count*question_options_count))
        return value if value > 0.0 else 0.0
    
    def __sum_value(self,answer,penalization_factor,total):
        if answer.is_correct:
            return 10/total
        else:
            return (-10)*penalization_factor/total
        
    def get_remaining_time(self):
        must_end = self.start_date + timedelta(minutes=self.autoevaluation.duration)
        difference = must_end - datetime.now()
        return difference.total_seconds() / 60
    
    def get_must_finish_time(self):
        must_end = self.start_date + timedelta(minutes=self.autoevaluation.duration)
        return must_end
    
    @staticmethod
    def get_last_calification(student,autoevaluation):
        califications = Calification.objects.filter(student=student,autoevaluation=autoevaluation).order_by('-end_date')
        return califications.first() if califications.exists() else None
    

class CourseStatus(models.Model):
    completed = models.BooleanField(verbose_name="¿Completado?")
    start_date = models.DateTimeField(verbose_name="Fecha de comienzo")
    student = models.ForeignKey(Student,on_delete=models.CASCADE,verbose_name="Estudiante")
    courses = models.ForeignKey(Course,on_delete=models.CASCADE,verbose_name="Cursos")

    def __str__(self) -> str:
        return str(self.completed)
    
    def get_remaining_days(self,course):
        duration = course.duration
        remaining_time = (self.start_date + timedelta(weeks=duration) - datetime.now(timezone.utc))
        return remaining_time.days
    
    @staticmethod
    def get_end_calification(student,course):
        units = CourseUnit.objects.filter(course=course)
        if not units.exists():
            return "-"
        autoevaluations = Autoevaluation.objects.filter(course_unit__in=units)
        if not autoevaluations.exists():
            return "-"
        
        califications = Autoevaluation.objects.filter(course_unit__in=units) \
            .values('pk','course_unit') \
            .annotate(last_calification=Coalesce(
                Subquery(
                    Calification.objects.filter(student=student,autoevaluation=OuterRef('pk')) \
                        .order_by('-end_date').values('calification')[:1]),-1.0)) \
            .values('last_calification') \
            .filter(last_calification__gte=0.0)
        
        if not califications.exists():
            return "-"
        calification_list = [c.get('last_calification') for c in califications]
        sum_calification = sum(calification_list)/len(calification_list)
        return sum_calification
