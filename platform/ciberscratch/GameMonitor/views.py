from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls \
    import reverse
from django.contrib.auth.decorators import login_required
from ciberscratch.forms import ProfileForm, RegisterUser, ClassroomForm
from django.contrib.auth.models import User
from .models import Classroom, Membership
from django.utils.translation import gettext


#################################################################################
@login_required(login_url='/accounts/login')
def home(request, ):
    if request.user.is_superuser:
        return HttpResponseRedirect(reverse('admin:index'))
    elif request.user.is_staff:
        classroom = Classroom.objects.filter(lecturer=request.user)
        return render(request, 'home.html', {'base_template': 'base.html',
                                             'view_url': 'home',
                                             'show_parent_name': True,
                                             'classrooms': classroom,
                                             'title': gettext('home'),
                                             'custom_view_name': 'select-cases-view'})
    else:
        return render(request, 'home.html', {'base_template': 'base.html',
                                             'view_url': 'home',
                                             'show_parent_name': True,
                                             'title': gettext('home'),
                                             'custom_view_name': 'select-cases-view'})


#################################################################################
####### GESTION CURSOS   ########################################################
#################################################################################
@login_required(login_url='/accounts/login')
def manage_classroom(request, class_id=0):
    if class_id == 0:
        clase = Classroom()
        clase.gen_access_key()
        clase.lecturer = request.user
    else:
        clase = Classroom.objects.get(id=class_id)

    form = ClassroomForm(instance=clase)
    if request.method == 'POST':
        form = ClassroomForm(data=request.POST, instance=clase)
        if form.is_valid():
            update = form.save(commit=False)
            update.save()
        return HttpResponseRedirect(reverse('home'))
    return render(request, "edit_classroom.html", {'base_template': 'base.html',
                                                   'view_url': 'classroom-manager',
                                                   'form': form,
                                                   'show_parent_name': True,
                                                   'title': gettext('Manage Class')})
#####################################################################################
@login_required(login_url='/accounts/login')
def delete_classroom(request, class_id=0):
    clase = Classroom.objects.get(id=class_id)
    if clase :
        clase.delete()
    return HttpResponseRedirect(reverse('admin:index'))
#################################################################################
####### GESTION USUARIOS ########################################################
#################################################################################
def register_user_with_code(request, ):
    if request.method == 'POST':
        form = RegisterUser(data=request.POST)
        if form.is_valid():
            clase = Classroom.objects.get(access_key=form.cleaned_data['classroom_key'])
            if clase is not None:
                user = User.objects.create_user(form.cleaned_data['username'], "", form.cleaned_data['password1'])
                user.save()
                miembro = Membership.objects.create(classroom=clase, student=user)
                miembro.save()
                return render(request, "user_register_done.html", {'base_template': 'base.html',
                                                                   'view_url': 'register_user',
                                                                   'title': gettext('Register User')
                                                                   })
            else:
                form.add_error('classroom_key', gettext('La clave no se corresponde con ninguna clase'))
    else:
        form = RegisterUser()
    return render(request, "user_register.html", {'base_template': 'base.html',
                                                  'view_url': 'register_user',
                                                  'form': form,
                                                  'title': gettext('Register User')
                                                  })


#################################################################################

@login_required(login_url='/accounts/login')
def update_profile(request, ):
    if request.method == 'POST':
        form = ProfileForm(data=request.POST, instance=request.user)
        if form.is_valid():
            update = form.save(commit=False)
            update.save()
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'edit_profile.html', {'base_template': 'base.html',
                                                 'view_url': 'update_profile',
                                                 'form': form,
                                                 })
