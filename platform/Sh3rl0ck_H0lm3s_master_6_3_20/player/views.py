import logging
from django.contrib.sites.shortcuts import get_current_site
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from importer.forms import SelectCourseForm
from .business import GroupBusiness, CourseBusiness, UserBusiness
from importer.importers import parse_data, USER_MODEL_TYPE

logger = logging.getLogger(__name__)


@login_required(login_url='/accounts/login/')
def course_list(request):
    logger.info("Pantalla de selección de asignatura.")
    if request.method == 'POST':
        group_selected = request.POST.get("item-selected", None)

        # Con el id del listado tenemos que obtener su correspondencia con bbdd
        course_selected = CourseBusiness.get_course_by_group_id(group_id=group_selected)

        logger.info("Se ha seleccinado asignatura: %s", course_selected)
        if course_selected:
            request.session['course_id'] = course_selected.id
            return redirect('game_list')
        else:
            messages.error(request, _('Debe seleccionar una asignatura'))

    current_user = request.user
    if current_user:
        # Buscamos los grupos del usuario
        groups = list()
        group_list = GroupBusiness.get_db_group_by_user(current_user)
        if not group_list or 0 == len(group_list):
            logger.warning("El usuario %s no está en ningun grupo. (userId: %d)" % (current_user.username,
                                                                                    current_user.id))
            messages.warning(request, _("El usuario no está asignado a ninguna asignatura."))
        else:
            paginator = Paginator(group_list, 3)
            page = request.GET.get('page')
            groups = paginator.get_page(page)

        return render(request, 'course_list.html', {'base_template': 'base.html',
                                                    'items': groups,
                                                    'title': _('Selección de Asignatura'),
                                                    # 'view_url': 'course_list',
                                                    'view_url': 'course_list',
                                                    'custom_view_name': 'select-course-view'})
    else:
        logger.error("Usuario no recuperado")
        messages.error(request, _("Usuario no recuperado"))
        return render(request, 'home.html', {})


@user_passes_test(lambda u: u.is_staff)
def user_group_management(request):
    form = SelectCourseForm()
    show_processing = False
    if request.session.get('user_xml_path', None):
        show_processing = True

    return render(request, 'users_management.html', {'form': form,
                                                     'title': _('Gestión de Grupos de Usuarios'),
                                                     'show_processing': show_processing})


@user_passes_test(lambda u: u.is_staff)
def course_selected(request, course_id=None, year=None, show_changed_msg=False):
    data = {'status': 'error'}
    user_xml_path = request.session.get('user_xml_path', None)

    if not course_id:
        course_id = request.POST.get('course_id', None)
    if not year:
        year = request.POST.get('year', None)
    if course_id and year:
        if user_xml_path:
            # Extraemos los datos del xml
            users = parse_data(xml_file=user_xml_path, model_type=USER_MODEL_TYPE)
            logger.debug("Fichero xml de usuarios %s" % users)
            del request.session['user_xml_path']
            current_site = get_current_site(request)
            for user in users.get_user():
                try:
                    # Damos de alta el usuario
                    django_user = UserBusiness.register_user(user, current_site)
                    # Creamos un grupo individual para el usuario
                    GroupBusiness.create_individual_group(course_id, year, django_user)
                except Exception as e:
                    messages.warning(request, e)

        # Recuperamos los grupos que no sean automaticos
        userGroups = GroupBusiness.get_not_autogroups_by_course_and_year(course_id=course_id, year=year)

        # Recuperar los grupos existentes para el curso-año
        groups_list = GroupBusiness.get_by_course_and_year(course_id=course_id, year=year)

        paginator = Paginator(groups_list, 10)
        page = request.GET.get('page')
        groups = paginator.get_page(page)

        data['group_table'] = render(request, 'users_group_form.html',
                                     {'items': groups, 'userGroups': userGroups, 'course_id': course_id,
                                      'year': year}).content.decode('utf-8')
        data['status'] = 'ok'

        if show_changed_msg:
            data['message'] = _("Cambio realizado con exito.")
    else:
        data['error'] = _("Rellene todos los campos obligatorios.")

    return JsonResponse(data)


@user_passes_test(lambda u: u.is_staff)
@require_POST
def group_enable_valuechange(request):
    group_id = request.POST.get('group_id', None)
    group = GroupBusiness.toggle_enable(group_id=group_id)
    logger.debug("Cambiado estado de activación del grupo %s" % group.name)
    return course_selected(request, course_id=group.course_id, year=group.year, show_changed_msg=True)


@user_passes_test(lambda u: u.is_staff)
@require_POST
def create_usergroup(request):
    group_name = request.POST.get('group_name', None)
    user_id = request.POST.get('user_id', None)
    course_id = request.POST.get('course_id', None)
    year = request.POST.get('year', None)

    logger.debug("Creación de nuevo grupo de usuario %s" % group_name)

    # Comprobamos que la asignatura existe
    if not course_id or not CourseBusiness.exists_course(course_id):
        logger.error("No ha sido posible recuperar la asignatura con id %s" % course_id)
        return JsonResponse({'status': 'error', 'error_msg': _("Ha ocurrido un problema al crear el grupo.")})

    if not year:
        logger.error("El año no ha sido especificado.")
        return JsonResponse({'status': 'error', 'error_msg': _("Ha ocurrido un problema al crear el grupo.")})

    # Recuperamos el usuario
    user = UserBusiness.get_user(user_id)
    if not user:
        logger.error("No ha sido posible recuperar el usuario con id %s" % user_id)
        return JsonResponse({'status': 'error', 'error_msg': _("Ha ocurrido un problema al crear el grupo.")})

    # Eliminamos al usuario del grupo al que pertenecia antes
    GroupBusiness.remove_user_from_group(course_id=course_id, year=year, user=user)

    # Creamos el grupo
    group = GroupBusiness.create_group(course_id, year, group_name)

    # Asignamos el usuario al nuevo grupo
    group.users.add(user)
    group.save()

    return course_selected(request, course_id=group.course_id, year=group.year, show_changed_msg=True)


@user_passes_test(lambda u: u.is_staff)
@require_POST
def change_usergroup(request):
    user_id = request.POST.get('user_id', None)
    group_id = request.POST.get('group_id', None)
    course_id = request.POST.get('course_id', None)
    year = request.POST.get('year', None)

    if not group_id:
        logger.error("No se ha especificado el grupo para el usuario con id %s" % user_id)
        return JsonResponse({'status': 'error', 'error_msg': _("Ha ocurrido un problema al cambiar de grupo.")})

    group_id = int(group_id)

    if not course_id:
        logger.error("No se ha especificado la asignatura para el usuario con id %s" % user_id)
        return JsonResponse({'status': 'error', 'error_msg': _("Ha ocurrido un problema al cambiar de grupo.")})

    if not year:
        logger.error("No se ha especificado el año para el usuario con id %s" % user_id)
        return JsonResponse({'status': 'error', 'error_msg': _("Ha ocurrido un problema al cambiar de grupo.")})

    # Recuperamos el usuario
    user = UserBusiness.get_user(user_id)
    if not user:
        logger.error("No ha sido posible recuperar el usuario con id %s" % user_id)
        return JsonResponse({'status': 'error', 'error_msg': _("Ha ocurrido un problema al cambiar de grupo.")})

    if 0 < group_id:
        # Recuperamos el curso nuevo
        new_group = GroupBusiness.get(group_id=group_id)
        if not new_group:
            logger.error("No ha sido posible recuperar el grupo con id %s" % group_id)
            return JsonResponse({'status': 'error', 'error_msg': _("Ha ocurrido un problema al cambiar de grupo.")})

    # Eliminamos al usuario del grupo al que pertenecia antes
    GroupBusiness.remove_user_from_group(course_id=course_id, year=year, user=user)

    # Si el grupo seleccionado es 0 quiere decir que el usuario debe estar solo
    if 0 == group_id:
        new_group = GroupBusiness.create_individual_group(course_id=course_id, year=year, django_user=user)
        if not new_group:
            logger.error("No se ha podido crear el grupo individual para el usuario con id %s" % user_id)
            return JsonResponse({'status': 'error', 'error_msg': _("Ha ocurrido un problema al cambiar de grupo.")})

    new_group.users.add(user)
    new_group.save()

    return course_selected(request, course_id=new_group.course_id, year=new_group.year, show_changed_msg=True)
