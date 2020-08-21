from django.db import models
from ..ciberscratch.validators import Validator

##############################################################
"""
Course representa una asignatura en el juego. 
"""


class Course(models.Model):
    name = models.CharField(max_length=200)
    acronym = models.CharField(max_length=8, blank=True, null=True)
    qualification = models.CharField(max_length=200)
    level = models.CharField(max_length=200)
    URL = models.URLField(max_length=512, blank=True, null=True)


    def __str__(self):
        return self.name


##############################################################
"""
Cada año académico tendremos una clase, es decir, un grupo de estudiantes. Las clases 
tendrá una dirección. 
"""


class Classroom(models.Model):
    name = models.CharField(max_length=200)
    acronym = models.CharField(max_length=200)
    access_key = models.CharField(max_length=64)
    groups_enabled = models.BooleanField(default=True)
    group_max_members = models.IntegerField(validators=[Validator.validate_positive_number], default=0)
    group_min_members = models.IntegerField(validators=[Validator.validate_positive_number], default=0)
    start_date = models.DateTimeField(blank=True, null=True)
    finish_date = models.DateTimeField(blank=True, null=True)
    creation_group_player_permission = models.BooleanField(default=True)

    # enlace a la asignatura
    course = models.ForeignKey(Course, on_delete=models.CASCADE)


##############################################################
class ClassGroup(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
