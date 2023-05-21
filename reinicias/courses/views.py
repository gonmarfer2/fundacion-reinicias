from django.shortcuts import render
from courses.models import Course,CourseUnit
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.core import serializers
import json
from django.db.models.expressions import Subquery
from django.db.models import Count, OuterRef
from django.db.models.functions import Coalesce 
from django.db import models

@require_http_methods(["GET"])
def list_course(request):
    unit_count = CourseUnit.objects.filter(course=OuterRef('pk')).values('course')
    available_courses = Course.objects.filter(preceeded_by__isnull=True).annotate(
        units=Coalesce(Subquery(
            unit_count.annotate(count=Count('pk')).values('count'),
            output_field=models.IntegerField()
            ),0))
    
    all_fields = [field.name for field in Course._meta.get_fields()] + ['units']
    # serialized_courses = serializers.serialize("json",available_courses,fields=all_fields)
    serialized_courses = list(available_courses.values(*all_fields))
    json_data = json.dumps(serialized_courses)
    context = {
        'courses':json_data,
        'userGroups':serializers.serialize("json",request.user.groups.all()),
        }
    return render(request,'courses/list.html',context)
