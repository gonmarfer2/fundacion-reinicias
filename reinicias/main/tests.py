from django.test import TestCase
from .models import User,Person,Technic,Teacher,Patient,PatientRecord,PatientRecordHistory,Diary,Notification
from django.contrib.auth.models import Group
import datetime
import json
from technics.models import INITIAL_PROBLEMS
from django.test import Client
from main.views import check_new_notifications,update_read_notifications

class BaseTestCase(TestCase):
    TECHNIC_TEAM = 'technics'
    TEACHER_TEAM = 'teachers'
    PATIENT_TEAM = 'patients'

    def setUp(self):
        superuser = User(
            email='reinicias@reinicias.com',
            username='superuser_test'
        )
        superuser.set_password('reinicias')
        superuser.is_staff = True
        superuser.is_superuser = True
        superuser.save()
        technic_group,_ = Group.objects.get_or_create(name=self.TECHNIC_TEAM)
        teacher_group,_ = Group.objects.get_or_create(name=self.TEACHER_TEAM)
        patient_group,_ = Group.objects.get_or_create(name=self.PATIENT_TEAM)
        superuser.groups.add(technic_group)
        superuser.groups.add(teacher_group)
        superuser.groups.add(patient_group)

        person = Person(
            user=superuser,
            name="Superuser",
            last_name="Reinicias",
            birth_date=datetime.date(1,1,1),
            telephone="+000000000",
            sex="O")
        person.save()

        technic = Technic.objects.create(person=person)
        teacher = Teacher.objects.create(person=person)
        superuser_patient = Patient.objects.create(person=person,school="Reinicias")
        superuser_patient_record = PatientRecord.objects.create(number='FR18000',patient=superuser_patient)
        PatientRecordHistory.objects.create(state='a',initial_problem=INITIAL_PROBLEMS[0][0],record=superuser_patient_record)

        Diary.objects.create(patient=superuser_patient)

        self.superuser = superuser
        self.superuser_person = person
        self.superuser_technic = technic
        self.superuser_teacher = teacher
        self.superuser_patient = superuser_patient
        self.client = Client()

    def tearDown(self):
        pass

    def login(self, user='superuser_test', password='reinicias'):
        response = self.client.post('/login/',{'username':'superuser_test','password':'reinicias'})
        self.assertTrue(response.status_code == 302)
        
class UserTestCase(BaseTestCase):
    def test_user(self):
        # self.superuser
        self.assertTrue(self.superuser.get_groups_display() == 'Paciente,Formador,Técnico',
                        'The roles of the user don\'t coincide')
        self.assertTrue(self.superuser.get_person() == self.superuser_person)
        self.assertTrue(self.superuser.get_patient() == self.superuser_patient)

        new_user = User(
            email = 'newuser@reinicias.com',
            username = 'newuser'
        )
        new_user.save()

        self.assertTrue(new_user.get_groups_display() == '',
                        'The roles of the user don\'t coincide')
        self.assertTrue(new_user.get_person() == None)
        self.assertTrue(new_user.get_patient() == None)

class NotificationTestCase(BaseTestCase):
    def test_notification(self):
        super().login()
        new_notis = self.client.get('/notifications/check/').json()
        self.assertTrue(new_notis['new'] == False)
        new_notification = Notification(
            type = 'Nueva notificación de prueba',
            user = self.superuser
        )
        new_notification.save()
        new_notis = self.client.get('/notifications/check/').json()
        self.assertTrue(new_notis['new'] == True)

        self.client.post('/notifications/read/',{'user_id':self.superuser.pk})
        self.assertTrue(Notification.objects.exclude(user=self.superuser,read_date__isnull=False).count() == 0)