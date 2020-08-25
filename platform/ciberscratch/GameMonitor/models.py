from django.db import models
from ciberscratch.validators import Validator
from django.contrib.auth.models import User
import datetime
from rstr import Rstr
from random import SystemRandom

##############################################################
"""
Course representa una asignatura en el juego. 
"""


class Course(models.Model):
    LEVELS = (
        ('G', 'GRADO'),
        ('M', 'MASTER'),
        ('P', 'FORMACIÓN PERMANENT'),
        ('MO', 'MOOC'),
        ('O', 'OTRO')
    )
    name = models.CharField(max_length=200)
    acronym = models.CharField(max_length=8, blank=True, null=True)
    qualification = models.CharField(max_length=200)
    level = models.CharField(max_length=200, choices=LEVELS)
    URL = models.URLField(max_length=512, blank=True, null=True)
    staff = models.ManyToManyField(User, through='Lecturers')

    def __str__(self):
        return "{0} ({1}-{2}). {3}".format(self.name, self.acronym, self.level, self.qualification)

    def classes(self):
        return Classroom.objects.filter(course__id=self.id)


##############################################################
class Lecturers(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lecturer = models.ForeignKey(User, validators=[Validator.is_lecturer], on_delete=models.CASCADE)
    joined_date = models.DateTimeField(default=datetime.datetime.now())


##############################################################
"""
Cada año académico tendremos una clase, es decir, un grupo de estudiantes. Las clases 
tendrá una dirección. 
"""


class Classroom(models.Model):
    name = models.CharField(max_length=200)
    acronym = models.CharField(max_length=200)
    access_key = models.CharField(max_length=64, unique=True)
    groups_enabled = models.BooleanField(default=True)
    group_max_members = models.IntegerField(validators=[Validator.validate_positive_number], default=1)
    group_min_members = models.IntegerField(validators=[Validator.validate_positive_number], default=1)
    start_date = models.DateTimeField(blank=True, null=True)
    finish_date = models.DateTimeField(blank=True, null=True)
    creation_group_player_permission = models.BooleanField(default=True)

    # enlace a la asignatura
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    # coordinador de la clase
    lecturer = models.ForeignKey(User, validators=[Validator.is_lecturer], related_name="creator",
                                 on_delete=models.CASCADE, null=True)

    # miembros de la clases
    student_body = models.ManyToManyField(User, through='Membership')

    def __str__(self):
        return "{0} ({1}; del {2} al {3})".format(self.name, self.acronym, self.start_date, self.finish_date)

    def gen_access_key(self):
        rs = Rstr(SystemRandom())
        self.access_key=rs.xeger(r'[A-Z]\d[A-Z]-\d[A-Z]\d')
        return self.access_key


#############################################################################################

class Membership(models.Model):
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE)
    student = models.ForeignKey(User, validators=[Validator.is_student], on_delete=models.CASCADE)
    joined_date = models.DateTimeField(default=datetime.datetime.now())


##############################################################
class ClassGroup(models.Model):
    name = models.CharField(max_length=200, default="")
    is_full = models.BooleanField(default=False)
    creation_date = models.DateField(blank=True, null=True)
    # grupo asociado a una clase
    classroom = models.ForeignKey(Classroom, on_delete=models.CASCADE, null=True)
    # grupo asociado a una asignatura
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True)
    # miembros del grupo
    participants = models.ManyToManyField(User)

    def __str__(self):
        return self.name
