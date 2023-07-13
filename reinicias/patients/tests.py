from django.test import TestCase
from technics.tests import TechnicBaseCaseTest
import patients.models as models
import datetime
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from time import sleep

class PatientBaseCaseTest(TechnicBaseCaseTest):
    def setUp(self):
        super().setUp()

        self.diary_entry =  models.DiaryEntry.objects.create(
            title='Test Diary Entry',
            content='This is a test diary entry',
            feeling='ira',
            diary=self.diary
        )

        self.task = models.Task.objects.create(
            title='Test Task',
            description='This is a test task',
            state='w',
            deadline=datetime.datetime.now(),
            patient=self.patient,
            technic=self.technic,
        )

class DiaryCaseTest(PatientBaseCaseTest):
    def test_create_diary_entry(self):
        super().login(user='test_patient',password='reinicias')
        before_count = models.DiaryEntry.objects.all().count()
        self.client.post(f'/patients/diary/{self.patient.get_person().pk}/create/',{
            'title':'New Test Diary Entry',
            'content':'This is a new test diary entry',
            'feeling':'ira',
        })
        after_count = models.DiaryEntry.objects.all().count()
        self.assertTrue(after_count == before_count + 1)

class TaskCaseTest(PatientBaseCaseTest):
    def test_add_task(self):
        super().login(user='test_technic',password='reinicias')
        before_count = models.Task.objects.filter(patient=self.patient,technic=self.technic).count()
        self.client.post(f'/patients/{self.patient.get_person().pk}/tasks/add/',{
            'title':'New Test Task',
            'description':'This is a new test task',
            'deadline':'14/12/2044',
        })
        after_count = models.Task.objects.filter(patient=self.patient,technic=self.technic).count()
        self.assertTrue(after_count == before_count + 1)

    def test_delete_task(self):
        super().login(user='test_technic',password='reinicias')
        before_count = models.Task.objects.filter(patient=self.patient,technic=self.technic).count()
        self.client.get(f'/patients/{self.patient.get_person().pk}/tasks/{self.task.pk}/delete/')
        after_count = models.Task.objects.filter(patient=self.patient,technic=self.technic).count()
        self.assertTrue(after_count == before_count - 1)

    def test_accept_task(self):
        super().login(user='test_technic',password='reinicias')
        self.task.state = 'c'
        self.task.save()

        self.client.get(f'/patients/{self.patient.get_person().pk}/tasks/{self.task.pk}/accept/')
        updated_task = models.Task.objects.get(pk=self.task.pk)
        self.assertTrue(updated_task.state == 'a')

    def test_deny_task(self):
        super().login(user='test_technic',password='reinicias')
        self.task.state = 'c'
        self.task.save()

        self.client.get(f'/patients/{self.patient.get_person().pk}/tasks/{self.task.pk}/deny/')
        updated_task = models.Task.objects.get(pk=self.task.pk)
        self.assertTrue(updated_task.state == 'w')


class PatientViewCaseTest(StaticLiveServerTestCase):
    def setUp(self):
        self.base = PatientBaseCaseTest()
        self.base.setUp()

        options = webdriver.ChromeOptions()
        options.headless = False
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1920,1080)


    def tearDown(self):
        self.driver.quit()
        self.ong = None
        super().tearDown()


    def login(self,username,password):
        self.driver.get(f'{self.live_server_url}/')
        self.driver.find_element(By.ID,'id-navlink-login').click()
        self.driver.find_element(By.ID,'id_username').send_keys(username)
        self.driver.find_element(By.ID,'id_password').send_keys(password)
        self.driver.find_element(By.ID,'id-submitLogin').click()

    
    def test_show_emotions(self):
        self.login("test_patient","reinicias")
        self.driver.find_element(By.ID,'id-navlink-feelings').click()
        sleep(1)
        graph = self.driver.find_elements(By.CSS_SELECTOR,'.plot-container.plotly')
        self.assertTrue(len(graph) == 1)

    def test_task_add(self):
        self.login("test_technic","reinicias")
        self.driver.get(f'{self.live_server_url}/patients/{self.base.patient.get_person().pk}/tasks/')
        accordion = self.driver.find_element(By.ID,'accordionPending')
        old_tasks = accordion.find_elements(By.CSS_SELECTOR,'.accordion-item.my-3')

        self.driver.find_element(By.ID,'id-new-entry').click()
        self.driver.find_element(By.ID,'id_title').send_keys('New Super Test Task')
        self.driver.find_element(By.ID,'id_description').send_keys('This is a new test task')
        self.driver.find_element(By.ID,'id_deadline').send_keys('14/12/9999')
        self.driver.find_element(By.CSS_SELECTOR,'.r-form-button').submit()

        accordion = self.driver.find_element(By.ID,'accordionPending')
        tasks = accordion.find_elements(By.CSS_SELECTOR,'.accordion-item.my-3')
        self.assertTrue(len(old_tasks) + 1 == len(tasks))
