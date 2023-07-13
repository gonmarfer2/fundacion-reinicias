from django.test import TestCase
from main.tests import BaseTestCase
from courses.models import Course, CourseStatus, CourseUnit, Autoevaluation, Student, Question, QuestionOption
from main.models import Teacher, Person, User, Group
import datetime
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from time import sleep

class CourseBaseTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()

        teacher_user = User.objects.create(
            username='test_teacher',
            email='teacher@reinicias.com'
        )
        teacher_user.set_password('reinicias')
        teacher_user.save()
        teacher_group,_ = Group.objects.get_or_create(name="teachers")
        teacher_user.groups.add(teacher_group)

        teacher_person = Person.objects.create(
            user=teacher_user,
            name='Teacher',
            last_name='Reinicias',
            birth_date=datetime.date(1,1,1),
            telephone='+34555555555',
            sex='O'
        )

        self.teacher = Teacher.objects.create(
            person=teacher_person,
        )

        self.course = Course.objects.create(
            name='Test Course',
            description='Test Course Description',
            published=False,
            duration=4,
            teacher=self.teacher
        )

        self.course_unit = CourseUnit.objects.create(
            title='Test Unit',
            order=1,
            course=self.course
        )

        self.autoevaluation = Autoevaluation.objects.create(
            title='Test Autoevaluation',
            duration=10,
            instructions='Test Autoevaluation Instructions',
            penalization_factor=0.25,
            course_unit=self.course_unit
        )

        self.question = Question.objects.create(
            question='Test Question',
            order=1,
            is_multiple=False,
            autoevaluation=self.autoevaluation
        )

        self.question_option = QuestionOption.objects.create(
            option_name='Test Option 1',
            is_correct=True,
            question=self.question
        )
        self.question_option2 = QuestionOption.objects.create(
            option_name='Test Option 2',
            is_correct=False,
            question=self.question
        )

        student_user = User.objects.create(
            username='test_student',
            email='student@reinicias.com'
        )
        student_user.set_password('reinicias')
        student_user.save()
        student_group,_ = Group.objects.get_or_create(name="students")
        student_user.groups.add(student_group)

        student_person = Person.objects.create(
            user=student_user,
            name='Student',
            last_name='Reinicias',
            birth_date=datetime.date(1,1,1),
            telephone='+34555555555',
            sex='O'
        )

        self.student = Student.objects.create(
            person=student_person,
        )

class CourseUnitsUnitTestCase(CourseBaseTestCase):

    def test_create_unit(self):
        super().login(user='test_teacher',password='reinicias')
        before_units = CourseUnit.objects.all().count()
        self.client.post(f'/courses/{self.course.pk}/units/create/',{
            'title':'Test Unit Creation'
        })
        after_units = CourseUnit.objects.all().count()
        self.assertTrue(before_units + 1 == after_units)


    def test_edit_unit(self):
        EDITED_TITLE = 'Test Course Edited'
        EDITED_ORDER = 5

        super().login(user='test_teacher',password='reinicias')
        self.client.post(f'/courses/{self.course.pk}/units/{self.course_unit.pk}/edit/',{
            'title':EDITED_TITLE,
            'order':EDITED_ORDER,
            'course':self.course.pk
        })
        edited_course_unit = CourseUnit.objects.get(pk=self.course_unit.pk)
        self.assertTrue(edited_course_unit.title == EDITED_TITLE)
        self.assertTrue(edited_course_unit.order == EDITED_ORDER)


    def test_edit_unit_fail(self):
        EDITED_TITLE = ''
        EDITED_ORDER = -1

        super().login(user='test_teacher',password='reinicias')
        self.client.post(f'/courses/{self.course.pk}/units/{self.course_unit.pk}/edit/',{
            'title':EDITED_TITLE,
            'order':EDITED_ORDER,
            'course':self.course.pk
        })
        edited_course_unit = CourseUnit.objects.get(pk=self.course_unit.pk)
        self.assertTrue(edited_course_unit.title == self.course_unit.title)
        self.assertTrue(edited_course_unit.order == self.course_unit.order)


    def test_delete_unit(self):
        super().login(user='test_teacher',password='reinicias')
        new_unit = CourseUnit.objects.create(
            title='Test Unit Deleted',
            order=10,
            course=self.course
        )

        old_pk = new_unit.pk
        self.client.get(f'/courses/{self.course.pk}/units/{new_unit.pk}/delete/')
        self.assertTrue(not CourseUnit.objects.filter(pk=old_pk).exists())


    def test_delete_unit_fail_not_exists(self):
        super().login(user='test_teacher',password='reinicias')
        
        response = self.client.get(f'/courses/{self.course.pk}/units/999/delete/')
        self.assertTrue(response.status_code == 404)


    def test_delete_unit_fail_published_course(self):
        super().login(user='test_teacher',password='reinicias')
        
        new_unit = CourseUnit.objects.create(
            title='Test Unit Deleted',
            order=10,
            course=self.course
        )

        self.course.published = True
        self.course.save()

        response = self.client.get(f'/courses/{self.course.pk}/units/{new_unit.pk}/delete/')
        self.assertTrue(response.status_code == 403)


class CoursesUnitTestCase(CourseBaseTestCase):

    NEW_COURSE_NAME = 'New Course'

    def test_inscribe_student(self):
        super().login(user='test_student',password='reinicias')
        self.client.get(f'/courses/{self.course.pk}/inscribe')
        new_enrol = CourseStatus.objects.filter(student=self.student,courses=self.course)
        self.assertTrue(new_enrol.exists() == True)

    
    def test_create_course(self):

        super().login(user='test_teacher',password='reinicias')
        self.client.post('/courses/create/',{
            'name':self.NEW_COURSE_NAME,
            'duration':12,
            'description':'This is a new course',
        })
        self.assertTrue(Course.objects.filter(name=self.NEW_COURSE_NAME).exists())


    def test_create_course_fail_(self):
        super().login(user='test_teacher',password='reinicias')
        self.client.post('/courses/create/',{
            'name':self.NEW_COURSE_NAME,
        })
        self.assertTrue(not Course.objects.filter(name=self.NEW_COURSE_NAME).exists())

    
    def test_edit_course(self):
        super().login(user='test_teacher',password='reinicias')
        self.client.post(f'/courses/{self.course.pk}/edit',{
            'name':self.NEW_COURSE_NAME,
            'duration':12,
            'description':'This is a new course',
            'course_id_edit':self.course.pk
        })
        edited_course = Course.objects.get(pk=self.course.pk)
        self.assertTrue(edited_course.name == self.NEW_COURSE_NAME)


    def test_delete_course(self):
        super().login(user='test_teacher',password='reinicias')
        old_pk = self.course.pk
        self.client.get(f'/courses/{old_pk}/delete')
        self.assertTrue(not Course.objects.filter(pk=old_pk).exists())


class CoursesViewTestCase(StaticLiveServerTestCase):
    def setUp(self):
        self.base = CourseBaseTestCase()
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
        self.driver.find_element(By.ID, 'id_username').send_keys("test_teacher")
        self.driver.find_element(By.ID, 'id_password').send_keys("reinicias")
        self.driver.find_element(By.ID, 'id-submitLogin').click()


    def test_course_list(self):
        self.login()
        self.driver.find_element(By.ID,'id-navlink-courses').click()
        count_courses = self.driver.find_element(By.ID,'accordionNonPublished').find_elements(By.CLASS_NAME,'accordion-item')
        self.assertTrue(len(count_courses) == 1)

        first_course = count_courses[0]
        first_course.click()
        accordion_buttons = first_course.find_elements(By.CLASS_NAME,'courses-button')
        sleep(1)
        see_course_btn = list(
            filter(lambda button: button.find_element(By.CSS_SELECTOR,'a > span') \
                   .get_attribute("innerHTML") == 'Ver curso', 
                   accordion_buttons))[0]
        see_course_btn.click()

        first_unit = self.driver.find_element(By.ID,'accordionUnits') \
            .find_elements(By.CLASS_NAME,'accordion-item')[0]
        first_unit.click()
        sleep(1)
        unit_buttons = first_unit.find_elements(By.CLASS_NAME,'courses-button')
        see_autoev_btn = list(
            filter(lambda button: button.find_element(By.CSS_SELECTOR,'a') \
                   .get_attribute("innerHTML") == 'Ver autoevaluación', 
                   unit_buttons))[0]
        see_autoev_btn.click()
        self.assertTrue(len(self.driver.find_elements(By.CLASS_NAME,'autoevaluation-instructions')) > 0)


