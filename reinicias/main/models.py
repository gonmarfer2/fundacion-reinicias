from django.db import models
from django.contrib.auth.models import AbstractUser,BaseUserManager, Group
from django.core.validators import RegexValidator
import datetime

TECHNIC_TEAM = 'technics'
TEACHER_TEAM = 'teachers'
PATIENT_TEAM = 'patients'

class UserManager(BaseUserManager):
    def create_superuser(self,email,password=None, **extra_fields):
        user = self.model(
            email=email,
            **extra_fields
        )
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        technic_group,_ = Group.objects.get_or_create(name=TECHNIC_TEAM)
        teacher_group,_ = Group.objects.get_or_create(name=TEACHER_TEAM)
        patient_group,_ = Group.objects.get_or_create(name=PATIENT_TEAM)
        user.groups.add(technic_group)
        user.groups.add(teacher_group)
        user.groups.add(patient_group)

        person = Person(
            user=user,
            name="Superuser",
            last_name="Reinicias",
            birth_date=datetime.date(1,1,1),
            telephone="+000000000",
            sex="O")
        person.save(using=self._db)

        Technic.objects.create(person=person)
        Teacher.objects.create(person=person)
        Patient.objects.create(person=person,school="Reinicias")

        print("This user can be manually configured through the admin site")

        return user

class User(AbstractUser):
    objects = UserManager()

    def has_group(self,group):
        return self.groups.filter(name=group).exists()


class Person(models.Model):
    SEX_CHOICES = [
        ('M','Masculino'),
        ('F','Femenino'),
        ('N','No binario'),
        ('O','Otro')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE,verbose_name="Usuario")
    name = models.CharField(max_length=255,verbose_name='Nombre')
    last_name = models.CharField(max_length=255,verbose_name='Apellidos')
    birth_date = models.DateField(verbose_name='Fecha de nacimiento')
    telephone = models.CharField(max_length=20,validators=[RegexValidator(regex=r"^\+?1?\d{9,15}$",message="El número de teléfono debe introducirse en el formato +999999999, hasta 15 cifras.")],verbose_name="Teléfono")
    sex = models.CharField(max_length=1,choices=SEX_CHOICES,verbose_name="Sexo/Género")

    def __str__(self) -> str:
        return f"{self.name} {self.last_name}"
    
    def get_user(self):
        return self.user
    
    def get_person(self):
        return self


class Technic(models.Model):
    person = models.OneToOneField(Person,on_delete=models.CASCADE)

    def __str__(self) -> str:
        return str(self.person)
    
    def get_user(self):
        return self.person.user
    
    def get_person(self):
        return self.person
    

class Teacher(models.Model):
    person = models.OneToOneField(Person,on_delete=models.CASCADE, verbose_name="Usuario")

    def __str__(self) -> str:
        return str(self.person)
    
    def get_user(self):
        return self.person.user
    
    def get_person(self):
        return self.person
    

class Patient(models.Model):
    person = models.OneToOneField(Person,on_delete=models.CASCADE, verbose_name="Usuario")
    school = models.CharField(max_length=255,verbose_name='Centro Educativo')

    def __str__(self) -> str:
        return str(self.person)
    
    def get_user(self):
        return self.person.user
    
    def get_person(self):
        return self.person