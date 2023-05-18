from django.db import models
from django.contrib.auth.models import AbstractUser,BaseUserManager, Group
from django.core.validators import RegexValidator

TECHNIC_TEAM = 'technics'

class UserManager(BaseUserManager):
    def create_superuser(self,email,password=None, **extra_fields):
        user = self.model(
            email=email,
            **extra_fields
        )
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True

        person = Person(user=user)
        while True:
            try:
                user_age = int(input("Edad del nuevo usuario: "))
                if user_age < 0:
                    raise ValueError
                person.age = user_age
                break
            except ValueError:
                print("No ha introducido un número o es menor que cero. Inténtelo de nuevo.")

        while True:
            try:
                user_age = int(input("Teléfono (+999999999): "))
                person.age = user_age
                break
            except ValueError:
                print("No ha introducido un número correcto. Debe tener el formato +999999999 con hasta 15 cifras. Inténtelo de nuevo.")

        user.save(using=self._db)
        technic_group,_ = Group.objects.get_or_create(name=TECHNIC_TEAM)
        user.groups.add(technic_group)
        person.save(using=self._db)

        return user

class User(AbstractUser):
    objects = UserManager()


class Person(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.PositiveIntegerField()
    telephone = models.CharField(max_length=20,validators=[RegexValidator(regex=r"^\+?1?\d{9,15}$",message="El número de teléfono debe introducirse en el formato +999999999, hasta 15 cifras.")])
