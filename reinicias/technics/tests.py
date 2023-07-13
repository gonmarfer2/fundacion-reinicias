from main.tests import BaseTestCase
import technics.models as models
from main.models import User, Person, Technic, Group
import datetime
from patients.models import Diary
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from time import sleep

class TechnicBaseCaseTest(BaseTestCase):

    def setUp(self):
        super().setUp()

        technic_user = User.objects.create(
            username='test_technic',
            email='technic@reinicias.com'
        )
        technic_user.set_password('reinicias')
        technic_user.save()
        technic_group,_ = Group.objects.get_or_create(name="technics")
        technic_user.groups.add(technic_group)

        technic_person = Person.objects.create(
            user=technic_user,
            name='Technic',
            last_name='Reinicias',
            birth_date=datetime.date(1,1,1),
            telephone='+34555555555',
            sex='O'
        )

        self.technic = Technic.objects.create(
            person=technic_person,
        )

        patient_user = User.objects.create(
            username='test_patient',
            email='patient@reinicias.com'
        )
        patient_user.set_password('reinicias')
        patient_user.save()
        patient_group,_ = Group.objects.get_or_create(name="patients")
        patient_user.groups.add(patient_group)

        patient_person = Person.objects.create(
            user=patient_user,
            name='Patient',
            last_name='Reinicias',
            birth_date=datetime.date(1,1,1),
            telephone='+34555555555',
            sex='O'
        )

        self.patient = models.Patient.objects.create(
            person=patient_person,
        )

        self.session = models.Session.objects.create(
            datetime=datetime.date.today(),
            title='Test Initial Session',
            is_initial=True,
            session_type='i',
            session_state='c',
            technic=self.technic
        )

        TEST_REPORT_FIELD = 'Test Report Field'

        self.initial_report = models.InitialReport.objects.create(
            record_number='FR18001',
            initial_problem='cov',
            name='Patient',
            last_name='Reinicias',
            treatment_type=TEST_REPORT_FIELD,
            first_evaluation=TEST_REPORT_FIELD,
            family_situation=TEST_REPORT_FIELD,
            social_situation=TEST_REPORT_FIELD,
            academic_situation=TEST_REPORT_FIELD,
            problem_situation=TEST_REPORT_FIELD,
            drug_history=TEST_REPORT_FIELD,
            leisure=TEST_REPORT_FIELD,
            labour_situation=TEST_REPORT_FIELD,
            social_diagnostic=TEST_REPORT_FIELD,
            answer_plan=TEST_REPORT_FIELD,
            observations=TEST_REPORT_FIELD,
            session=self.session
        )

        self.patient_record = models.PatientRecord.objects.create(
                number=self.initial_report.record_number,
                patient=self.patient
            )

        self.patient_record_history_entry = models.PatientRecordHistory.objects.create(
            state='a',
            initial_problem=self.initial_report.initial_problem,
            record=self.patient_record
        )

        self.diary = Diary.objects.create(
            patient=self.patient
        )


class PatientCreationTestCase(TechnicBaseCaseTest):
    def test_create_patient(self):
        super().login(user='test_technic',password='reinicias')
        NEW_TEST_REPORT_FIELD = 'New Test Report Field'

        new_session = models.Session.objects.create(
            datetime=datetime.date(2023,8,14),
            title='Test New Initial Session',
            is_initial=True,
            session_type='i',
            session_state='c',
            technic=self.technic
        )

        new_initial_report = models.InitialReport.objects.create(
            record_number='FR18002',
            initial_problem='cov',
            name='Patient2',
            last_name='Reinicias2',
            treatment_type=NEW_TEST_REPORT_FIELD,
            first_evaluation=NEW_TEST_REPORT_FIELD,
            family_situation=NEW_TEST_REPORT_FIELD,
            social_situation=NEW_TEST_REPORT_FIELD,
            academic_situation=NEW_TEST_REPORT_FIELD,
            problem_situation=NEW_TEST_REPORT_FIELD,
            drug_history=NEW_TEST_REPORT_FIELD,
            leisure=NEW_TEST_REPORT_FIELD,
            labour_situation=NEW_TEST_REPORT_FIELD,
            social_diagnostic=NEW_TEST_REPORT_FIELD,
            answer_plan=NEW_TEST_REPORT_FIELD,
            observations=NEW_TEST_REPORT_FIELD,
            session=new_session
        )

        self.client.post(f'/technics/sessions/{new_session.pk}/reports/{new_initial_report.pk}/register/',{
            'username':'patient2',
            'birth_date':datetime.date(2000,1,1),
            'password1':'r31n1c14s',
            'password2':'r31n1c14s',
            'name':new_initial_report.name,
            'last_name':new_initial_report.last_name,
            'email':'patient2@reinicias.com',
            'telephone':'+34555555555',
            'sex':'O',
            'roles':'Paciente',
            'school':'Test School',
        })

        self.assertTrue(models.Patient.objects.filter(person__user__username='patient2').exists())


class TechnicViewsCaseTest(StaticLiveServerTestCase):
    def setUp(self):
        self.base = TechnicBaseCaseTest()
        self.base.setUp()

        options = webdriver.ChromeOptions()
        options.headless = True
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1920,1080)


    def tearDown(self):
        self.driver.quit()
        self.ong = None
        super().tearDown()


    def login(self):
        self.driver.get(f'{self.live_server_url}/')
        self.driver.find_element(By.ID,'id-navlink-login').click()
        self.driver.find_element(By.ID, 'id_username').send_keys("test_technic")
        self.driver.find_element(By.ID, 'id_password').send_keys("reinicias")
        self.driver.find_element(By.ID, 'id-submitLogin').click()
    
    def test_users(self):
        self.login()
        self.driver.find_element(By.ID,'id-navlink-users').click()
        users = self.driver.find_elements(By.TAG_NAME,'tr')
        
        BEFORE_USERS = 4
        sleep(1)
        self.assertTrue(len(users) == BEFORE_USERS)

        self.driver.find_element(By.CSS_SELECTOR,'.autoevaluation-button.courses-button-cyan').click()
        self.driver.find_element(By.ID,'id_username').send_keys('technic2')
        self.driver.find_element(By.ID,'id_email').send_keys('technic2@reinicias.com')
        self.driver.find_element(By.ID,'id_password1').send_keys('r31n1c14s')
        self.driver.find_element(By.ID,'id_password2').send_keys('r31n1c14s')
        self.driver.find_element(By.ID,'id_birth_date').send_keys('01/01/2000')
        self.driver.find_element(By.ID,'id_name').send_keys('Technic2')
        self.driver.find_element(By.ID,'id_last_name').send_keys('Reinicias')
        self.driver.find_element(By.ID,'id_telephone').send_keys('+34555555555')
        self.driver.find_element(By.ID,'id_roles_1').click()
        self.driver.find_element(By.CSS_SELECTOR,'.r-form-button').submit()

        sleep(1)
        self.driver.find_element(By.ID,'id-navlink-users').click()
        users = self.driver.find_elements(By.TAG_NAME,'tr')
        sleep(1)
        self.assertTrue(len(users) == BEFORE_USERS+1)

        users[1].click()

        CHANGED_NAME = 'Technic2Changed'
        self.driver.find_elements(By.CSS_SELECTOR,'.autoevaluation-button.courses-button-cyan')[0].click()
        self.driver.find_element(By.ID,'id_name').clear()
        self.driver.find_element(By.ID,'id_name').send_keys(CHANGED_NAME)
        self.driver.find_element(By.CSS_SELECTOR,'.r-form-button').submit()

        changed_name_div = self.driver.find_elements(By.CSS_SELECTOR,'.list-group-item')[2]
        changed_name = self.driver.execute_script("return arguments[0].lastChild.textContent;",changed_name_div).strip()
        self.assertTrue(changed_name == CHANGED_NAME)