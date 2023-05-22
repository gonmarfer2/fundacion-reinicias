from django.shortcuts import render, redirect
from courses.models import Course,CourseUnit,Student
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.core import serializers
from django.contrib.auth.models import Group
import json
from django.db.models.expressions import Subquery
from django.db.models import Count, OuterRef
from django.db.models.functions import Coalesce 
from django.db import models, transaction
from .forms import StudentRegisterForm
from main.models import Person

@require_http_methods(["GET"])
def list_course(request):
    context = {}
    template = 'courses/list_anonymous.html'
    unit_count = CourseUnit.objects.filter(course=OuterRef('pk')).values('course')
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
    return render(request,template,context)

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
