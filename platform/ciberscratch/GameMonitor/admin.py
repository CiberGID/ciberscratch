from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(Course)
admin.site.register(Classroom)
admin.site.register(ClassGroup)
admin.site.register(Lecturers)
admin.site.register(Membership)