from django.db import models
from main.models import Person, Teacher
from django.core.validators import MaxValueValidator, MinValueValidator
from datetime import datetime, timezone, timedelta
import re

class Course(models.Model):
    # Existe el atributo error_messages para los campos que permite poner errores personalizados para claves por defecto
    name = models.CharField(max_length=256,blank=False,verbose_name="Nombre")
    description = models.TextField(blank=False,verbose_name="Descripción")
    published = models.BooleanField(verbose_name="Publicado")
    duration = models.IntegerField(validators=[MinValueValidator(1)],verbose_name="Duración")
    teacher = models.ForeignKey(Teacher,on_delete=models.CASCADE,verbose_name="Formador")
    index_document = models.FileField(upload_to='course/%Y/%m/%d',null=True,verbose_name="Índice de curso")
    preceeded_by = models.ManyToManyField("self",blank=True,symmetrical=False,verbose_name="Predecesores")
    creation_date = models.DateTimeField(auto_now_add=True,verbose_name='Fecha de creación')
    # Tengo que validar que un curso A precedido por B no pueda preceder a B

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
            )]

class Autoevaluation(models.Model):
    title = models.CharField(max_length=256,blank=False,verbose_name="Título")
    duration = models.PositiveIntegerField(verbose_name="Duración")
    instructions = models.TextField(blank=False,verbose_name="Instrucciones")
    penalization_factor = models.DecimalField(max_digits=3,decimal_places=2,validators=[MinValueValidator(0.0),MaxValueValidator(1.0)],verbose_name="Factor de penalización")
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

class QuestionOption(models.Model):
    option_name = models.CharField(max_length=256,verbose_name="Opción")
    order = models.PositiveSmallIntegerField(verbose_name="Orden")
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

class Calification(models.Model):
    calification = models.PositiveSmallIntegerField(null=True,validators=[MaxValueValidator(10)],verbose_name="Calificación")
    start_date = models.DateTimeField(verbose_name="Fecha de comienzo")
    end_date = models.DateTimeField(verbose_name="Fecha de finalización")
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
                    value += self.__sum_value(answer,self.autoevaluation.penalization_factor,questions_count)
            else:
                question_options_count = QuestionOption.objects.filter(question=question).count()
                for answer in students_answers:
                    value += self.__sum_value(answer,self.autoevaluation.penalization_factor,(questions_count*question_options_count))
        return value
    
    def __sum_value(self,answer,penalization_factor,total):
        if answer.is_correct:
            return 1/total
        else:
            return (-1)*penalization_factor/total


class CourseStatus(models.Model):
    completed = models.BooleanField(verbose_name="¿Completado?")
    start_date = models.DateTimeField(verbose_name="Fecha de comienzo")
    student = models.ForeignKey(Student,on_delete=models.CASCADE,verbose_name="Estudiante")
    courses = models.ForeignKey(Course,on_delete=models.CASCADE,verbose_name="Cursos")

    def __str__(self) -> str:
        return str(self.completed)
    
    def get_remaining_days(self,course):
        this_units = CourseUnit.objects.filter(course=course)
        remaining_time = (self.start_date + timedelta(days=this_units.count() * 7)) - datetime.now(timezone.utc)
        return remaining_time.days
