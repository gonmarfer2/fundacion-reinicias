from django.shortcuts import render, redirect
from courses.models import Course,CourseUnit,CourseUnitResource,Student,Calification,CourseStatus
from django.views.decorators.http import require_http_methods
from django.core import serializers
from django.contrib.auth.models import Group
import json
from django.db.models.expressions import Subquery
from django.db.models import Count, OuterRef, Exists, F
from django.db.models.functions import Coalesce 
from django.db import models, transaction
from .forms import StudentRegisterForm, CourseUnitCreateForm, CourseUnitEditForm, CourseCreateForm, CourseUnitResourceCreateForm, CourseEditForm
from main.models import Person, Teacher
from django.contrib.auth.decorators import user_passes_test
from datetime import datetime, timezone
from django.core.exceptions import PermissionDenied
from django.http import Http404

# CUSTOM DECORATOR

def group_required(*group_names):
    def has_group(user):
        if user.is_authenticated:
            if user.groups.filter(name__in=set(group_names)).exists() or user.is_superuser:
                return True
        return False
    return user_passes_test(has_group, login_url='login')

# CONSTANTS

ERROR_404_COURSE = "No existe ese curso"

# VIEWS

@require_http_methods(["GET"])
def list_course(request):
    unit_count = CourseUnit.objects.filter(course=OuterRef('pk')).values('course')
    if request.user.is_anonymous:
        available_courses = Course.objects.filter(published=True).filter(preceeded_by__isnull=True).annotate(
            units=Coalesce(Subquery(
                unit_count.annotate(count=Count('pk')).values('count'),
                output_field=models.IntegerField()
                ),0))

        context = {
            'courses':available_courses,
            'userGroups':serializers.serialize("json",request.user.groups.all()),
            }
        return render(request,'courses/list_anonymous.html',context)
    elif request.user.has_group('students'):
        this_person = Person.objects.get(user=request.user)
        this_student = Student.objects.get(person=this_person)
        current_courses = Course.objects.filter(published=True).filter(coursestatus__completed=False,coursestatus__student=this_student).annotate(
            units=Coalesce(Subquery(
                unit_count.annotate(count=Count('pk')).values('count'),
                output_field=models.IntegerField()
                ),0))
        done_courses = Course.objects.filter(published=True).filter(coursestatus__completed=True,coursestatus__student=this_student).annotate(
            units=Coalesce(Subquery(
                unit_count.annotate(count=Count('pk')).values('count'),
                output_field=models.IntegerField()
                ),0))

        rest_of_courses = Course.objects.filter(published=True).exclude(pk__in=current_courses).exclude(pk__in=done_courses)
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
    elif request.user.has_group('teachers'):
        published_courses = Course.objects.filter(published=True).annotate(
            units=Coalesce(Subquery(
                unit_count.annotate(count=Count('pk')).values('count'),
                output_field=models.IntegerField()
                ),0))
        non_published_courses = Course.objects.filter(published=False).annotate(
            units=Coalesce(Subquery(
                unit_count.annotate(count=Count('pk')).values('count'),
                output_field=models.IntegerField()
                ),0))
        
        context = {
            'publishedCourses':published_courses,
            'nonPublishedCourses':non_published_courses,
            'userGroups':request.user.groups.all(),
        }
        
        return render(request,'courses/list_teachers.html',context)


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
            return redirect("/")
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
            start_date=datetime.now(timezone.utc),
            student=this_student,
            courses=this_course
        )
        new_try.save()
        return redirect(f"/courses/{course_id}")

@require_http_methods(["GET"])
@group_required("students","teachers")
def details_course(request,course_id):
    if Course.objects.filter(pk=course_id).count() == 0:
        raise Http404(ERROR_404_COURSE)
    elif request.user.has_group('students'):
        this_person = Person.objects.get(user=request.user)
        this_student = Student.objects.get(person=this_person)
        this_course = Course.objects.get(pk=course_id)
        this_units = CourseUnit.objects.filter(course=this_course)

        completed_units = Calification.objects \
                .filter(student=this_student,autoevaluation__course_unit__in=this_units) \
                .values('autoevaluation__course_unit') \
                .annotate(total=Count('autoevaluation__course_unit')) \
                .order_by('total')
        
        this_units = this_units.annotate(completed=Coalesce(Exists(
                completed_units.filter(autoevaluation__course_unit=OuterRef('pk'))
            ),False),
            calification=Coalesce(
                Subquery(Calification.objects \
                        .filter(student=this_student,autoevaluation__course_unit=OuterRef('pk')) \
                        .order_by('-end_date') \
                        .values('calification')[:1]),None)).order_by('order')
        current_calification = CourseStatus.get_end_calification(student=this_student,course=course_id)

        unit_contents = {u.pk:CourseUnitResource.objects.filter(course_unit=u) for u in this_units}
        unit_block = {}
        if this_units.count() > 0:
            unit_block = {this_units.get(order=1).pk:False}
            for i in range(2,len(this_units)+1):
                if this_units.get(order=(i-1)).calification is None:
                    unit_block[this_units.get(order=(i)).pk] = True
                else:
                    unit_block[this_units.get(order=(i)).pk] = False

        remaining_days = CourseStatus.objects.get(student=this_student,courses=this_course).get_remaining_days(this_course)

        context = {
            'course':this_course,
            'units':this_units,
            'completedUnits':completed_units,
            'unitContents':unit_contents,
            'unitShow':unit_block,
            'currentCalification':current_calification,
            'remainingDays': remaining_days,
            'userGroups':request.user.groups.all()
        }
        return render(request,'courses/details.html',context)
    elif request.user.has_group('teachers'):
        this_course = Course.objects.get(pk=course_id)
        this_units = CourseUnit.objects.filter(course=this_course).order_by('order')
        unit_contents = {u.pk:CourseUnitResource.objects.filter(course_unit=u) for u in this_units}

        context = {
            'course':this_course,
            'units':this_units,
            'unitContents':unit_contents,
            'userGroups':request.user.groups.all(),
        }
        return render(request,'courses/details_teachers.html',context)
    
@require_http_methods(["GET","POST"])
@group_required("teachers")
@transaction.atomic()
def create_unit(request,course_id):
    if Course.objects.filter(pk=course_id).count() == 0:
        raise Http404(ERROR_404_COURSE)
    
    form = CourseUnitCreateForm()
    if request.method == "POST":
        form = CourseUnitCreateForm(request.POST)
        if form.is_valid():
            form_data = form.cleaned_data
            this_course = Course.objects.get(pk=course_id)
            new_order = CourseUnit.objects.filter(course=this_course).order_by('-order')
            new_order = new_order.first().order + 1 if new_order else 1
            new_unit = CourseUnit(
                title = form_data.get('title'),
                order = new_order,
                course = this_course
            )
            new_unit.save()

            return redirect(f'/courses/{course_id}')
    context = {
        'title':'AÑADIR TEMA',
        'userGroups':request.user.groups.all(),
        'form':form
    }
    return render(request,'units/register.html',context)

@require_http_methods(["GET","POST"])
@group_required("teachers")
@transaction.atomic()
def edit_unit(request,course_id,unit_id):
    if Course.objects.filter(pk=course_id).count() == 0:
        raise Http404(ERROR_404_COURSE)
    if CourseUnit.objects.filter(pk=unit_id).count() == 0:
        raise Http404(ERROR_404_COURSE)
    if Course.objects.get(pk=course_id).published == True:
        raise PermissionDenied()
    
    this_unit = CourseUnit.objects.get(pk=unit_id)
    form = CourseUnitEditForm(instance=this_unit)
    if request.method == "POST":
        form = CourseUnitEditForm(request.POST)

        if form.is_valid():
            form_data = form.cleaned_data

            old_order = this_unit.order
            this_unit.title = form_data.get('title')
            this_unit.order = form_data.get('order')
            this_unit.course = form_data.get('course')
            this_unit.save()

            reorder_course_units(course_id,this_unit,form_data.get('order'),old_order)

            return redirect(f'/courses/{course_id}')
        
        elif 'Course unit with this Curso and Orden already exists.' in form.errors.get('__all__',[]):
            
            form.clean()
            form_data = form.cleaned_data
            old_order = this_unit.order
            this_unit.title = form_data.get('title')
            this_unit.order = form_data.get('order')
            this_unit.course = form_data.get('course')
            this_unit.save()

            data_order = form_data.get('order')
            reorder_course_units(course_id,this_unit,data_order,old_order)
            
            return redirect(f'/courses/{course_id}')
        
    context = {
        'title':'EDITAR TEMA',
        'userGroups':request.user.groups.all(),
        'form':form
    }
    return render(request,'units/register.html',context)

def reorder_course_units(course_id,this_unit,new_order,old_order):
    if CourseUnit.objects.filter(course=course_id, order=new_order).exists():
        # Reorder other units
        if new_order < old_order:
            CourseUnit.objects.filter(course=course_id,order__gte=new_order,order__lt=old_order).exclude(pk=this_unit.pk).order_by('-order').update(order=F('order')+1)
        elif new_order > old_order:
            CourseUnit.objects.filter(course=course_id,order__gt=new_order).exclude(pk=this_unit.pk).order_by('-order').update(order=F('order')+1)
            CourseUnit.objects.filter(course=course_id,order__gt=old_order,order__lte=new_order).exclude(pk=this_unit.pk).order_by('order').update(order=F('order')-1)

@require_http_methods(["GET"])
@group_required("teachers")
@transaction.atomic()
def delete_unit(request,course_id,unit_id):
    if Course.objects.filter(pk=course_id).count() == 0:
        raise Http404(ERROR_404_COURSE)
    if CourseUnit.objects.filter(pk=unit_id).count() == 0:
        raise Http404(ERROR_404_COURSE)
    if Course.objects.get(pk=course_id).published == True:
        raise PermissionDenied()
    
    this_person = Person.objects.get(user=request.user)
    this_teacher = Teacher.objects.get(person=this_person)
    if Course.objects.filter(pk=course_id).first().teacher != this_teacher:
        raise PermissionDenied()
    
    this_unit = CourseUnit.objects.get(pk=unit_id)
    old_order = this_unit.order
    this_unit.delete()
    CourseUnit.objects.filter(course=course_id,order__gt=old_order).update(order=F('order')-1)

    return redirect(f'/courses/{course_id}/')

@require_http_methods(["GET","POST"])
@group_required("teachers")
@transaction.atomic()
def create_course(request):
    form = CourseCreateForm()
    if request.method == "POST":
        form = CourseCreateForm(request.POST,request.FILES)
        if form.is_valid():
            form_data = form.cleaned_data
            this_person = Person.objects.get(user=request.user)
            this_teacher = Teacher.objects.get(person=this_person)

            new_duration = form_data.get('duration') if form_data.get('duration') else Course.DEFAULT_COURSE_DURATION
            new_course = Course(
                name=form_data.get('name'),
                description=form_data.get('description'),
                published=False,
                duration=new_duration,
                teacher=this_teacher,
                index_document=form_data.get('index_document')
            )

            new_course.save()
            new_course.preceeded_by.set(form_data.get('preceeded_by'))
            return redirect(f'/courses/{new_course.pk}')

    context = {
        'title':'AÑADIR CURSO',
        'userGroups':request.user.groups.all(),
        'form':form
    }
    return render(request,'courses/create.html',context)

@require_http_methods(["GET","POST"])
@group_required("teachers")
@transaction.atomic()
def edit_course(request,course_id):
    if Course.objects.filter(pk=course_id).count() == 0:
        raise Http404(ERROR_404_COURSE)
    if Course.objects.get(pk=course_id).published == True:
        raise PermissionDenied()
    
    this_course = Course.objects.get(id=course_id)
    form = CourseEditForm(course_id_edit=course_id,initial={
        'course_id_edit':course_id,
        'name':this_course.name,
        'description':this_course.description,
        'index_document':this_course.index_document,
        'published':this_course.published,
        'duration':this_course.duration,
        'preceeded_by':this_course.preceeded_by.exclude(id=this_course.pk)
    })
    if request.method == "POST":
        form = CourseEditForm(request.POST,request.FILES,course_id_edit=course_id)
        if form.is_valid():
            form_data = form.cleaned_data
            this_person = Person.objects.get(user=request.user)
            this_teacher = Teacher.objects.get(person=this_person)

            new_duration = form_data.get('duration') if form_data.get('duration') else Course.DEFAULT_COURSE_DURATION
            update_course = Course.objects.filter(id=course_id)
            update_course.update(
                name=form_data.get('name'),
                description=form_data.get('description'),
                published=form_data.get('published'),
                duration=new_duration,
                teacher=this_teacher,
                index_document=form_data.get('index_document')
            )

            update_course = update_course.first()
            update_course.preceeded_by.set(form_data.get('preceeded_by'))
            return redirect(f'/courses/{update_course.pk}')

    context = {
        'title':'EDITAR CURSO',
        'userGroups':request.user.groups.all(),
        'form':form
    }
    return render(request,'courses/create.html',context)

@require_http_methods(["GET"])
@group_required("teachers")
@transaction.atomic()
def delete_course(request,course_id):
    if Course.objects.filter(pk=course_id).count() == 0:
        raise Http404(ERROR_404_COURSE)
    if Course.objects.get(pk=course_id).published == True:
        raise PermissionDenied()
    
    this_person = Person.objects.get(user=request.user)
    this_teacher = Teacher.objects.get(person=this_person)
    if Course.objects.filter(pk=course_id).first().teacher != this_teacher:
        raise PermissionDenied()
    
    Course.objects.get(pk=course_id).delete()

    return redirect('course_list')

@require_http_methods(["GET"])
@group_required("teachers")
@transaction.atomic()
def unpublish_course(request,course_id):
    if Course.objects.filter(pk=course_id).count() == 0:
        raise Http404(ERROR_404_COURSE)
    if Course.objects.get(pk=course_id).published == False:
        raise PermissionDenied()
    
    Course.objects.filter(pk=course_id).update(published=False)

    return redirect('course_list')

@require_http_methods(["GET","POST"])
@group_required("teachers")
@transaction.atomic()
def add_unit_resources(request,course_id,unit_id):
    if Course.objects.filter(pk=course_id).count() == 0:
        raise Http404(ERROR_404_COURSE)
    if CourseUnit.objects.filter(pk=unit_id).count() == 0:
        raise Http404(ERROR_404_COURSE)
    if Course.objects.get(pk=course_id).published == True:
        raise PermissionDenied()
    
    form = CourseUnitResourceCreateForm()
    if request.method == "POST":
        form = CourseUnitResourceCreateForm(request.POST, request.FILES)
        if form.is_valid():
            
            this_unit = CourseUnit.objects.get(pk=unit_id)

            new_resource = form.save(commit=False)
            new_resource.course_unit = this_unit
            new_resource.save()

            return redirect(f'/courses/{course_id}')

    context = {
        'title':'AÑADIR RECURSO',
        'userGroups':request.user.groups.all(),
        'form':form
    }
    return render(request,'unitresources/register.html',context)

@require_http_methods(["GET"])
@group_required("teachers")
@transaction.atomic()
def remove_unit_resources(course_id,unit_id,resource_id):
    if Course.objects.filter(pk=course_id).count() == 0:
        raise Http404(ERROR_404_COURSE)
    if CourseUnit.objects.filter(pk=unit_id).count() == 0:
        raise Http404(ERROR_404_COURSE)
    if CourseUnitResource.objects.filter(pk=resource_id).count() == 0:
        raise Http404(ERROR_404_COURSE)
    if Course.objects.get(pk=course_id).published == True:
        raise PermissionDenied()
    
    CourseUnitResource.objects.filter(pk=resource_id).delete()

    return redirect(f'/courses/{course_id}/')

@require_http_methods(["GET"])
@group_required("teachers")
def list_course_students(request,course_id):
    if Course.objects.filter(pk=course_id).count() == 0:
        raise Http404(ERROR_404_COURSE)
    
    this_course = Course.objects.get(id=course_id)
    students = CourseStatus.objects.filter(courses__id=course_id).order_by('-start_date')
    course_students = {s:CourseStatus.get_end_calification(s.student,course_id) for s in students}

    context = {
        'course':this_course,
        'students':course_students,
        'userGroups':request.user.groups.all()
    }

    return render(request,'courses/course_students.html',context)
