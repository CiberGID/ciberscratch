import logging

from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator

from .models import Group, UserGroup, Course
from django.contrib.auth.models import User, Group as AuthGroup
from django.contrib.auth.hashers import make_password
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

PROFESSOR_ROL = 'Profesorado'


class GroupBusiness:
    @staticmethod
    def get(group_id):
        try:
            return Group.objects.get(id=group_id)
        except Exception:
            return None

    @staticmethod
    def get_db_group_by_user(user):
        user_id = user.id
        player_groups = UserGroup.objects.filter(player_id=user_id, group__enabled=True)
        if not player_groups:
            logger.info("El usuario %s no esta asociado a ningun grupo", user_id)
            return None

        logger.debug("Player_groups %s", player_groups)
        groups = list()
        for pg in player_groups:
            if pg.group.enabled:
                groups.append(pg.group)

        return groups

    @staticmethod
    def get_by_course_and_user(course_id, user_id):
        return Group.objects.filter(course_id=course_id, usergroup__player_id=user_id, enabled=True)

    @staticmethod
    def get_by_course_and_user_and_year(course_id, user_id, year):
        return Group.objects.filter(course_id=course_id, usergroup__player_id=user_id, year=year)

    @staticmethod
    def create_individual_group(course_id, year, django_user):
        group = GroupBusiness.get_by_course_and_user_and_year(course_id, django_user.id, year)
        if group.exists():
            group = group[0]
            # Si ya existe grupo pero estaba desactivado lo volvemos a activar
            if not group.enabled:
                group.enabled = True
                group.save()
        else:
            # Generamos grupos individual
            group = Group.objects.create(name=django_user.username, course_id=course_id, year=year)
            group.users.add(django_user)
            group.save()
        return group

    @staticmethod
    def create_group(course_id, year, group_name):
        group = Group.objects.filter(name=group_name, course_id=course_id, year=year)
        if group.exists():
            group = group[0]
            # Si ya existe grupo pero estaba desactivado lo volvemos a activar
            if not group.enabled:
                group.enabled = True
                group.save()
        else:
            # Generamos grupos individual
            group = Group.objects.create(name=group_name, course_id=course_id, year=year)
        return group

    @staticmethod
    def get_by_course_and_year(course_id, year):
        return Group.objects.filter(course_id=course_id, year=year).order_by('name')

    @staticmethod
    def get_not_autogroups_by_course_and_year(course_id, year):
        # Obtenemos los usuarios de los grupos para el curso y año
        usernames = User.objects.filter(group__course_id=course_id, group__year=year).values_list('username', flat=True)
        # Recuperamos los grupos para el curso y año que no sean automaticamente individuales
        return Group.objects.filter(course_id=course_id, year=year).exclude(name__in=usernames).order_by('name')

    @staticmethod
    def toggle_enable(group_id):
        group = Group.objects.get(id=group_id)
        group.enabled = not group.enabled
        group.save()
        return group

    @staticmethod
    def remove_user_from_group(course_id, year, user):
        groups = Group.objects.filter(course_id=course_id, year=year, users__exact=user.id)
        if groups:
            for group in groups:
                group.users.remove(user)
                if 0 == group.users.all().count():
                    group.delete()


class CourseBusiness:
    @staticmethod
    def exists_course(course_id):
        return Course.objects.filter(id=course_id).exists()

    @staticmethod
    def get_player_courses(user):
        user_id = user.id
        groups = GroupBusiness.get_db_group_by_user(user)
        if groups and 0 < len(groups):
            courses = list()
            for group in groups:
                courses.append(group.course)
        else:
            logger.info("El usuario %s no esta asociado a ningun curso", user_id)
            return None
        return courses

    @staticmethod
    def get_course_by_group_id(group_id):
        group = Group.objects.filter(id=group_id, enabled=True)
        if not group:
            logger.error("No se ha encontrado el grupo con id %s", group_id)
            return None

        return group[0].course


class UserBusiness:
    @staticmethod
    def get_user(user_id):
        try:
            return User.objects.get(id=user_id)
        except Exception:
            return None

    @staticmethod
    def register_user(user, current_site):
        username = user.username
        email = user.email_address
        is_staff = user.is_professor

        django_user = User.objects.filter(username=username, email=email)
        if django_user:
            return django_user[0]
        else:
            # Verificamos que no exista un usuario con el mismo username y distinto email
            if User.objects.filter(username=username).exists():
                logger.error(
                    'No se puede dar de alta el usuario %s, ya existe en bbdd con un email diferente.' % username)
                raise ValueError(_(
                    'No se puede dar de alta el usuario %s, ya existe en bbdd con un email diferente.') % username)

            # Damos de alta el usuario
            password = User.objects.make_random_password()
            password_hasher = make_password(password=password)
            new_user = User.objects.create(username=username, email=email, is_staff=is_staff, password=password_hasher,
                                           is_active=True)
            UserBusiness.send_register_user_email(new_user, password, current_site)

            # Asignamos el rol de profesor si corresponde
            if is_staff:
                rol = AuthGroup.objects.get(name=PROFESSOR_ROL)
                rol.user_set.add(new_user)

            return new_user

    @staticmethod
    def send_register_user_email(new_user, password, current_site):
        site_name = current_site.name
        domain = current_site.domain
        use_https = False
        extra_email_context = None

        context = {
            'email': new_user.email,
            'domain': domain,
            'site_name': site_name,
            'password': password,
            'uid': urlsafe_base64_encode(force_bytes(new_user.pk)),
            'user': new_user,
            'token': default_token_generator.make_token(new_user),
            'protocol': 'https' if use_https else 'http',
            **(extra_email_context or {}),
        }
        subject = render_to_string('registration/new_user_subject.txt', context)
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        html_message = render_to_string('registration/new_user.html', context)

        send_mail(subject, '', 'admin@sherlock.es', [new_user.email], fail_silently=True,
                  html_message=html_message)

        logger.debug("Usuario %s creado. Enviado correo electronico con credenciales." % new_user.username)
