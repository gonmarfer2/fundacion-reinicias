from django.shortcuts import render, redirect
from courses.models import Course,CourseUnit,Student,CourseStatus
from django.views.decorators.http import require_http_methods
from django.core import serializers
from django.contrib.auth.models import Group
import json
from django.db.models.expressions import Subquery
from django.db.models import Count, OuterRef
from django.db.models.functions import Coalesce 
from django.db import models, transaction
from .forms import StudentRegisterForm
from main.models import Person
from django.contrib.auth.decorators import user_passes_test
import datetime
from django.core.exceptions import PermissionDenied

# CUSTOM DECORATOR

def group_required(*group_names):
    def has_group(user):
        if user.is_authenticated:
            if user.groups.filter(name__in=group_names).exists() or user.is_superuser:
                return True
        return False
    return user_passes_test(has_group, login_url='403')

# VIEWS

@require_http_methods(["GET"])
def list_course(request):
    unit_count = CourseUnit.objects.filter(course=OuterRef('pk')).values('course')
    if request.user.groups.filter(name="students").exists():
        this_person = Person.objects.get(user=request.user)
        this_student = Student.objects.get(person=this_person)
        current_courses = Course.objects.filter(coursestatus__completed=False,coursestatus__student=this_student).annotate(
            units=Coalesce(Subquery(
                unit_count.annotate(count=Count('pk')).values('count'),
                output_field=models.IntegerField()
                ),0))
        done_courses = Course.objects.filter(coursestatus__completed=True,coursestatus__student=this_student).annotate(
            units=Coalesce(Subquery(
                unit_count.annotate(count=Count('pk')).values('count'),
                output_field=models.IntegerField()
                ),0))

        rest_of_courses = Course.objects.exclude(pk__in=current_courses).exclude(pk__in=done_courses)
        for course in rest_of_courses:
            predecessors = course.preceeded_by.all()
            if predecessors is not None and not set(predecessors).issubset(set(done_courses)):
                rest_of_courses = rest_of_courses.exclude(pk=course.pk)
        rest_of_courses = rest_of_courses.annotate(
            units=Coalesce(Subquery(
                unit_count.annotate(count=Count('pk')).values('count'),
                output_field=models.IntegerField()
                ),0))

        context = {
            'currentCourses':current_courses,
            'doneCourses':done_courses,
            'restOfCourses':rest_of_courses,
            'userGroups':request.user.groups.all()
        }
        return render(request,'courses/list_students.html',context)

    else:
        available_courses = Course.objects.filter(preceeded_by__isnull=True).annotate(
            units=Coalesce(Subquery(
                unit_count.annotate(count=Count('pk')).values('count'),
                output_field=models.IntegerField()
                ),0))

        all_fields = [field.name for field in Course._meta.get_fields()] + ['units']
        serialized_courses = list(available_courses.values(*all_fields))
        json_data = json.dumps(serialized_courses)
        context = {
            'courses':json_data,
            'userGroups':serializers.serialize("json",request.user.groups.all()),
            }
        return render(request,'courses/list_anonymous.html',context)

@require_http_methods(["GET","POST"])
@transaction.atomic()
def register_student(request):
    form = StudentRegisterForm()
    if request.method == "POST":
        form = StudentRegisterForm(request.POST)
        if form.is_valid():
            # Create USER
            user = form.save(commit=False)
            user.save()
            student_group,_ = Group.objects.get_or_create(name="students")
            user.groups.add(student_group)

            form_data = form.cleaned_data
            # Create PERSON
            person = Person(
                user=user,
                name=form_data.get('name'),
                last_name=form_data.get('last_name'),
                birth_date=form_data.get('birth_date'),
                telephone=form_data.get('telephone'),
                sex=form_data.get('sex')
                )
            person.save()

            student = Student(
                person=person,
            )
            student.save()

            form.save()
            return(redirect("/"))
    context = {
        'userGroups':request.user.groups.all(),
        'form':form
    }
    return render(request,'register_student.html',context)

@require_http_methods(["GET"])
@group_required("students")
@transaction.atomic()
def inscribe_in_course(request,course_id):
    this_person = Person.objects.get(user=request.user)
    this_student = Student.objects.get(person=this_person)
    this_course = Course.objects.get(pk=course_id)
    if CourseStatus.objects.filter(student=this_student,courses=this_course).exists():
        raise PermissionDenied
    else:
        new_try = CourseStatus(
            completed=False,
            start_date=datetime.datetime.now(),
            student=this_student,
            courses=this_course
        )
        new_try.save()
        return redirect(f"/courses/{course_id}")
