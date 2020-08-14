import os
from django.db import models
from django.contrib.auth.models import User
from .validators import Validator


def get_image_path(instance, filename):
    path = 'photos'
    if isinstance(instance, Course):
        path = 'courses'
    return os.path.join(path, str(instance.id), filename)


# Create your models here.
class Department(models.Model):
    name = models.CharField(max_length=64)
    url = models.URLField(max_length=512, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Course(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    course_image = models.ImageField(upload_to=get_image_path, blank=True, null=True)
    acronym = models.CharField(max_length=8, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Group(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    year = models.IntegerField(validators=[Validator.validate_year])
    name = models.CharField(max_length=64)
    enabled = models.BooleanField(default=True)
    users = models.ManyToManyField(User, through='player.UserGroup')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-year', 'name']


class UserGroup(models.Model):
    player = models.ForeignKey(User, null=False, blank=False, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, null=False, blank=False, on_delete=models.CASCADE)

    class Meta:
        unique_together = (("player", "group"),)
