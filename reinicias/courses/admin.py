from django.contrib import admin
import courses.models as models

admin.site.register(models.Course)
admin.site.register(models.CourseUnitResource)
admin.site.register(models.CourseUnit)
admin.site.register(models.Autoevaluation)
admin.site.register(models.Question)
admin.site.register(models.QuestionOption)
admin.site.register(models.Student)
admin.site.register(models.Teacher)
admin.site.register(models.Calification)
admin.site.register(models.CourseStatus)