from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from GameMonitor.models import Classroom
from django.utils.translation import gettext


######################################################
class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'email']


######################################################
class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ['name', 'acronym', 'groups_enabled', 'group_max_members', 'group_min_members', 'start_date',
                  'finish_date', 'creation_group_player_permission','course']


######################################################
class RegisterUser(UserCreationForm):
    classroom_key = forms.CharField(label=gettext("Clave de la clase"), max_length=64)
