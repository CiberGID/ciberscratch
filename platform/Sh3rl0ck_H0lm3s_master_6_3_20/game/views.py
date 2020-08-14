import logging
import os
import shutil
import uuid
import hmac
import hashlib
import json
import re

from itertools import chain
from operator import attrgetter
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator
from django.http import JsonResponse, FileResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_sameorigin
from zipfile import ZipFile

from .decorators import user_with_game_and_case_permission, user_with_event_permission
from game.models import Game, GroupArtifactInfo, GroupGameCase, Case, Message, Story, Contact, Conversation, \
    StoryTypeEnum, ChatMessage, Event, PlayerRating
from player.models import UserGroup, Group, Course
from player.business import GroupBusiness
import guacamole.utils as docker_utils
from .business import GroupGameCaseBusiness, GroupArtifactInfoBusiness, HiddenInfoBusiness, GroupResponseBusiness, \
    GroupEventBusiness, ConversationBusiness, PlayerRatingBusiness, LearnTrackBusiness
from .forms import KeyCodeForm, EventResponseForm
from .utils import text_params_binding, extract_zipfile
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)

DOCKER_CONFIG_BUILD_HACKS_PATTERN = '({%\\s*hackResources\\s*%})'
DOCKER_CONFIG_BUILD_PARAMS_KEY = 'build_params'


@login_required(login_url='/accounts/login/')
def home(request, is_started=True):
    logger.info("Accediendo a la home")

    if request.method == 'POST':
        pass
    
    user_groups = GroupBusiness.get_db_group_by_user(request.user)
    # Obtenemos todos casos del usuario en el estado indicado
    my_ggc = list()
    group_game_cases = list()
    if user_groups:
        for group in user_groups:
            my_ggc.append(
                GroupGameCaseBusiness.get_own_cases(group_id=group.id, only_active_cases=is_started))

        paginator = Paginator(sorted(
            chain(*my_ggc),
            key=attrgetter('start_date')), 3)
        page = request.GET.get('page')
        group_game_cases = paginator.get_page(page)
        
    if not request.session.get('first_login'):
        LearnTrackBusiness.register_activity(user_id=request.user.id, code=101,description="Inicio de sesión")
        request.session['first_login']=True
    return render(request, 'case_list.html', {'base_template': 'base.html',
                                              'items': group_game_cases,
                                              'view_url': 'case_list',
                                              'show_parent_name': True,
                                              'is_started': is_started,
                                              'show_tabsheet': True,
                                              'custom_view_name': 'select-cases-view'})


@login_required(login_url='/accounts/login/')
def started_cases(request):
    return home(request, True)


@login_required(login_url='/accounts/login/')
def finished_cases(request):
    return home(request, False)


@login_required(login_url='/accounts/login/')
def game_list(request):
    logger.info("Pantalla de selección de juego")
    #Hemos seleccionado un juego
    if request.method == 'POST':
        user_id = request.user.id
        game_selected = request.POST.get("item-selected", None)
        logger.info("Usuario %s ha seleccinado juego: %s", user_id, game_selected)
        
        if game_selected:
            request.session['game_id'] = game_selected
            course_id = request.session.get('course_id', None)
            player_group = UserGroup.objects.filter(player_id=user_id, group__course_id=course_id) \
                .select_related('group')
            
            
            if player_group:
                logger.debug("group: " + str(player_group[0].group.id))
                request.session['group_id'] = player_group[0].group.id
                # activamos el juego para el estudiante
                GroupGameCaseBusiness.activate_game(player_group[0].group.id,game_selected)
                LearnTrackBusiness.register_activity(user_id=user_id,code=201,related_to=game_selected,description="El usuario en el grupo {0} ha decidido unirse al juego {1}".format(player_group[0].group.id,game_selected))
            else:
                logger.error("No se ha encontrado player group para el juego %s y usuario %s", game_selected, user_id)
                
            return redirect('case_list')
        else:
            messages.error(request, _('Debe seleccionar un juego'))

    course_id = request.POST.get("course", None)
    if not course_id:
        course_id = request.session.get('course_id', None)

    games = list()
    course = None
    if course_id:
        course = Course.objects.get(id=course_id)
        # Buscamos los juegos que tiene la asignatura
        game_list = Game.objects.filter(course__id=course_id, is_published=True)
        paginator = Paginator(game_list, 3)
        page = request.GET.get('page')
        games = paginator.get_page(page)

    return render(request, 'game_list.html', {'base_template': 'base.html',
                                              'items': games,
                                              'course': course,
                                              'title': _('Selección de Juego'),
                                              'view_url': 'game_list',
                                              'custom_view_name': 'select-games-view'})


@login_required(login_url='/accounts/login/')
def case_list(request):
    logger.info("Pantalla de selección de caso")
    game_id = request.POST.get('game_id', None)
    if not game_id:
        game_id = request.session.get('game_id', None)
    group_id = request.session.get('group_id', None)
    if request.method == 'POST':
        group_game_case_id = request.POST.get("item-selected")

        try:
            # Si nos viene en negativo se trata del identificador del caso
            if group_game_case_id:
                group_game_case_id = int(group_game_case_id)
                if 0 > group_game_case_id:
                    ggc = GroupGameCase.objects.get(group_id=group_id, game_id=game_id, case_id=group_game_case_id * -1)
                    group_game_case = ggc
                else:
                    group_game_case = GroupGameCase.objects.get(id=group_game_case_id)
                group_game_case_id = group_game_case.id
                logger.debug("Caso seleccionado %s. ggc: %s", group_game_case.case_id, group_game_case_id)

            request.session['group_game_case_id'] = group_game_case_id

            protocol = group_game_case.protocol
            # Comprobamos si el contenedor está arrancado
            container = docker_utils.start_container(protocol=protocol,
                                                     image_name=group_game_case.docker_image_name,
                                                     container_name=group_game_case.docker_container_name)
            if not container:
                raise ValueError(
                    _('No se ha levantado ningún contenedor para la imagen %s' % group_game_case.docker_image_name))

            if container.name != group_game_case.docker_container_name:
                group_game_case.docker_container_name = container.name
                group_game_case.save()

            expose_port = docker_utils.get_container_expose_port(container=container, protocol=protocol)
            logger.debug("Levantado contenedor %s con nombre %s en el puerto %s", group_game_case.docker_image_name,
                         container.name, expose_port)

            if not group_game_case.start_date:
                group_game_case.start_date = timezone.now()
                group_game_case.save()

            guacamole_param = {
                'protocol': group_game_case.protocol,
                'hostname': settings.GUACD_HOST,
                'port': expose_port,
                'username': group_game_case.username,
                'password': group_game_case.password
            }
            request.session['guacamole_case_config'] = guacamole_param

            return redirect('game_view')
        except Exception as e:
            logger.error(e)
            messages.error(request=request,
                           message=_("Se ha producido un error inesperado. Pruebe de nuevo pasado unos instantes."))

    group_game_cases = list()
    game = None
    if game_id:
        game = Game.objects.get(id=game_id)
        # Buscamos los casos que tiene el juego
        # Buscamos lso GroupGameCase del usuario para el juego
        if group_id:
            ggc = GroupGameCaseBusiness.get_by_group_and_game(group_id=group_id, game_id=game_id)

            # de los ggc aquellos que no tengan id le asignamos el id del caso pero en negativo
            for group_game_case in ggc:
                if not group_game_case.id:
                    group_game_case.id = group_game_case.case.id * -1
                    group_game_case.id = group_game_case.case.id * -1

            paginator = Paginator(ggc, 3)
            page = request.GET.get('page')
            group_game_cases = paginator.get_page(page)

    return render(request, 'case_list.html', {'base_template': 'base.html',
                                              'items': group_game_cases,
                                              'title': _('Selección de caso'),
                                              'show_breadcrumb': True,
                                              'view_url': 'case_list',
                                              'game': game,
                                              'custom_view_name': 'select-cases-view'})


@login_required(login_url='/accounts/login/')
def game_view(request):
    logger.info("Pantalla de juego")

    artifacts = list()
    contacts = list()
    conversation = None
    # Buscamos las pruebas activas
    group_game_case_id = request.session.get('group_game_case_id', None)
    if group_game_case_id:
        group_game_case_id = int(group_game_case_id)
        if 0 > group_game_case_id:
            group_id = request.session.get('group_id', None)
            game_id = request.session.get('game_id', None)
            group_game_case = GroupGameCaseBusiness.get_by_group_game_and_case(group_id=group_id, game_id=game_id,
                                                                               case_id=group_game_case_id * -1)
            request.session['group_game_case_id'] = group_game_case.id
        else:
            group_game_case = GroupGameCase.objects.get(id=group_game_case_id)

        # Si es una petición de refresco del chat procesamos unicamente esa parte
        if request.method == 'POST':
            message_id = request.POST.get('message_id', None)
            conversation_id = request.POST.get('conversation_id', None)
            contact_id = request.POST.get('contact_id', None)
            if message_id or conversation_id or contact_id:
                # Recuperamos los contactos del chat
                contacts = Contact.objects.filter(group_game_case_id=group_game_case_id)

                # Recuperamos las conversaciones del chat
                conversation = None

                if conversation_id or contact_id:
                    if conversation_id:
                        conversations = Conversation.objects.filter(group_game_case_id=group_game_case_id,
                                                                    id=conversation_id)
                    elif contact_id:
                        # Si nos llega el contacto es porque se quiere cargar el chat de dicho contacto
                        conversations = Conversation.objects.filter(group_game_case_id=group_game_case_id,
                                                                    contact_id=contact_id)
                    if conversations:
                        conversation = conversations[0]

                # Si nos llega el message_id es porque la historia esta solicitando el envio de un nuevo mensaje
                if message_id:
                    message = Message.objects.get(id=message_id)
                    # En este punto no se deberia haber recuperado la conversación todavia
                    conversation = ConversationBusiness.add_story_message_to_conversation(
                        group_game_case_id=group_game_case_id, message_id=message_id)

                if conversation:
                    chat_messages = conversation.chatmessage_set.all().order_by('date_message')
                    template = 'chat_panel.html'
                    data = {'base_template': 'empty_template.html',
                            'contacts': contacts,
                            'conversation': conversation,
                            'chat_messages': chat_messages
                            }

                    # Marcamos como leidos todos los mensajes
                    # _mark_as_read(conversation.id)

                    return render(request, template, data)
                    # chat_messages_render

        artifact_list = GroupArtifactInfoBusiness.get_active_artifacts(group_game_case.id)

        paginator = Paginator(artifact_list, 2)
        page = request.GET.get('page')
        artifacts = paginator.get_page(page)

        # Comprobamos si el caso tiene perosnajes para mostrar el icono del chat
        show_chat = GroupGameCase.objects.filter(id=group_game_case_id, case__event__characters__isnull=False).exists()
        if show_chat:
            # Recuperamos los contactos del chat
            contacts = Contact.objects.filter(group_game_case_id=group_game_case_id)

    else:
        logger.error("game_view: group_game_case_id no esta definido en la sesión.")

    key_form = KeyCodeForm(request.POST)
    comment_response_form = EventResponseForm(request.POST)

    template = 'game_view.html'
    data = {'base_template': 'empty_template.html',
            'form': key_form,
            'comment_form': comment_response_form,
            'items': artifacts,
            'ggc': group_game_case,
            'title': _('Pruebas'),
            'is_game_view': True,
            'show_chat': show_chat,
            'contacts': contacts,
            'conversation': conversation,
            'view_url': 'game_view',
            'custom_view_name': 'artifacts-panel'}

    # Si venia de post es porque era una petición de refresco sobre las pruebas
    if request.method == 'POST':
        template = 'clue_bar.html'
        data = {'base_template': 'empty_template.html',
                'items': artifacts,
                'title': _('Pruebas'),
                'view_url': 'game_view',
                'custom_view_name': 'artifacts-panel'}

    # return render(request, 'game_view.html', {'base_template': 'empty_template.html',
    return render(request, template, data)


@login_required(login_url='/accounts/login/')
@user_with_game_and_case_permission
def case_ranking(request, case_id=None):
    logger.info("Pantalla de ranking")

    group_id = None
    group = Group.objects.filter(usergroup__player_id=request.user.id, course__game__case__id=case_id)
    if group:
        group_id = group[0].id
    title = ''
    my_item_id = None
    items = None
    if group_id:
        # if case_id and group_id:

        case = Case.objects.get(id=case_id)
        if not case:
            logger.error("Caso %s no encontrado.", case_id)
            messages.error(request, _("Caso %s no encontrado." % case_id))
            return redirect('home')

        my_item_id = 0
        title = _('Clasificación del caso %s' % case.name)
        # Obtenemos el case del usuario
        group_game_case = GroupGameCase.objects.filter(case_id=case_id, group_id=group_id)
        if group_game_case:
            my_item_id = group_game_case[0].id

        # Sacamos todos los groupGameCase para el caso
        group_game_cases = GroupGameCaseBusiness.get_case_classification(case_id=case_id)
        paginator = Paginator(group_game_cases, 10)
        page = request.GET.get('page')
        items = paginator.get_page(page)

    return render(request, 'case_ranking.html', {'items': items,
                                                 'my_item_id': my_item_id,
                                                 'title': title})


@login_required(login_url='/accounts/login/')
@require_POST
def validate_key_code(request):
    data = {'status': 'error'}
    form = KeyCodeForm(request.POST)
    key_code = form.data.get('key_code')
    group_game_case_id = request.session.get('group_game_case_id', None)
    if key_code:
        try:
            info_key = uuid.UUID(str(key_code))
        except (AttributeError, ValueError):
            info_key = str(key_code)

        if info_key:
            if group_game_case_id:
                # Verificamos que la clave pertenece a una historia que no es de tipo chat
                # ya que las de tipo chat se validan en otro metodo
                db_group_artifact_info = GroupArtifactInfoBusiness.validate_key_info(
                    group_game_case_id=group_game_case_id, info_key=info_key)

                if not db_group_artifact_info:
                    data['error'] = _('El código introducido no es válido.')
                else:
                    valid_group_artifact_info = None
                    if db_group_artifact_info:
                        for group_artifact_info in db_group_artifact_info:
                            event = group_artifact_info.group_event.event
                            if not event.event_intro_story or event.event_intro_story.story_type.name != StoryTypeEnum.CHAT.value:
                                valid_group_artifact_info = group_artifact_info
                                break

                    if not valid_group_artifact_info:
                        data['error'] = _('El código introducido no es válido.')
                    elif not valid_group_artifact_info.is_artifact_active:
                        data['error'] = _('El código introducido no es válido en este momento.')
                    else:
                        # Validamos que la respuesta no se hubiese dado antes
                        has_response = GroupResponseBusiness.has_response(group_game_case_id=group_game_case_id,
                                                                          group_artifact_info_id=valid_group_artifact_info.id)

                        if has_response:
                            data['error'] = _('Este código ya ha sido validado.')
                        else:
                            data['status'] = 'ok'
                            data['group_artifact_info_id'] = valid_group_artifact_info.id
                            data['artifact_name'] = valid_group_artifact_info.artifact.name
                            data['key_code'] = str(valid_group_artifact_info.info_key)
                            data['score'] = valid_group_artifact_info.hidden_info.score
            else:
                data['error'] = _('Error de configuración. Vuelva a seleccionar el caso.')
    else:
        data['error'] = _('Este campo es requerido.')

    return JsonResponse(data)


@login_required(login_url='/accounts/login/')
@require_POST
def add_response(request):
    data = {'status': 'error'}
    if request.POST:
        response_form = EventResponseForm(request.POST)

        group_artifact_info_id = response_form.data.get('group_artifact_info')
        comment = response_form.data.get('comment')

        # Volcamos la respuesta del jugador
        group_artifact_info = GroupArtifactInfo.objects.get(id=group_artifact_info_id)
        hidden_info = GroupResponseBusiness.add_response(group_artifact_info_id=group_artifact_info.id,
                                                         player_comment=comment)

        group_game_case = group_artifact_info.group_game_case
        group_event = GroupEventBusiness.check_finish_event_response(group_game_case.id,
                                                                     hidden_info_id=hidden_info.id)

        data['status'] = 'ok'
        data['group_game_case_id'] = group_artifact_info.group_game_case.id
        data['case_id'] = group_game_case.case.id
        if group_event:
            event = group_event.event
            data['event'] = event.id
            if event.event_end_story:
                data['end_event_story'] = event.event_end_story.id
        else:
            data['message'] = _(
                '¡Bien hecho! Pero no es la clave necesaria para continuar la historia. Sigue buscando.')

    return JsonResponse(data)


def _stop_docker_container(group_game_case_id):
    if group_game_case_id:
        try:
            ggc = GroupGameCase.objects.get(id=group_game_case_id)
            if ggc.docker_container_name:
                docker_utils.stop_container(container_name=ggc.docker_container_name, commit=True,
                                            image_name=ggc.docker_image_name)
        except Exception as e:
            logger.error(e)


@login_required(login_url='/accounts/login/')
def stop_docker_container_and_logout(request):
    logger.debug('procediendo a parar contenedor y cerrar sesion')
    
    _stop_docker_container(group_game_case_id=request.session.get('group_game_case_id', None))
    LearnTrackBusiness.register_activity(request.user.id,102,"Cierre de sesión")
    return redirect('/accounts/logout')


@login_required(login_url='/accounts/login/')
def exit_game(request):
    logger.debug("saliendo del juego")
    group_game_case_id = request.session.get('group_game_case_id', None)
    if group_game_case_id:
        ggc = GroupGameCase.objects.get(id=group_game_case_id)
        _stop_docker_container(group_game_case_id=group_game_case_id)
        return redirect('case_ranking', case_id=ggc.case_id)

    return redirect('home')


@login_required(login_url='/accounts/login/')
@require_POST
def generate_container(request):
    def _generate_container_user_passwd(username):
        return hmac.new(key=bytearray(settings.DOCKER_CONTAINER_SECRET_KEY, 'utf-8'),
                        msg=bytearray(username, 'utf-8'),
                        digestmod=hashlib.sha256).hexdigest()

    def _generate_case_container(docker_image_name, case, username, password, group_game_case_id):
        # Comprobamos si el base_img_path es un zip o un simple dockerfile
        relative_base_img_path, extension = os.path.splitext(case.base_img_path)
        dockerfile = None
        dockerfile_file = None
        dockerfile_params = None
        unzip_path = None
        if '.zip' == extension.lower():
            zip_filename = os.path.join(settings.MEDIA_ROOT, case.base_img_path)
            with ZipFile(zip_filename) as base_case:
                # Extraemos el contenido del zip
                unzip_path = os.path.join(settings.MEDIA_ROOT, relative_base_img_path)
                extract_zipfile(extraction_path=unzip_path, zip_file=base_case)
                base_case.close()

                # recuperamos el dockerfile y el fichero de configuración
                try:
                    dockerfile_file = open(os.path.join(unzip_path, 'Dockerfile'), 'r+')
                    dockerfile = dockerfile_file.read()  # .decode('utf-8')
                    with open(os.path.join(unzip_path, 'config.json'), 'rb') as base_dockerfile_config:
                        dockerfile_params = json.load(base_dockerfile_config)
                        logger.debug("dockerfile_params = %s", dockerfile_params)
                except Exception as err:
                    logger.error(err)
        else:
            dockerfile = case.base_img_path
        logger.debug("El fichero dockerfile es {0}".format(dockerfile))
        # Procedemos a hacer los hacks definidos en bbdd
        hacks_commands = HiddenInfoBusiness.get_hack_commands(case_id=case.id, group_game_case_id=group_game_case_id)
        if hacks_commands:
            # Si el dockerfile tiene el tag hacksResources lo sustituimos, sino añadimos los comandos al final
            hack_keys = re.findall(DOCKER_CONFIG_BUILD_HACKS_PATTERN, dockerfile)
            if hack_keys:
                for hack_key in hack_keys:
                    dockerfile = dockerfile.replace(hack_key, hacks_commands)
            else:
                dockerfile += hacks_commands

        build_args = None
        if dockerfile_params:
            # Procesamos el dockerfile personalizandolo con el fichero de configuración
            dockerfile = text_params_binding(text=dockerfile, params=dockerfile_params)

            # Leemos los parametros que se deben pasar al build
            if DOCKER_CONFIG_BUILD_PARAMS_KEY in dockerfile_params:
                build_args = dockerfile_params[DOCKER_CONFIG_BUILD_PARAMS_KEY]

            # Añadimos los parametros de usuario y contraseña
            build_args['username'] = username
            build_args['password'] = password
            logger.debug("build_args: %s", build_args)

        docker_utils.write_dockerfile(dockerfile_file=dockerfile_file, content=dockerfile)
        logger.debug(dockerfile)

        # Construimos la imagen docker
        logger.info("Se procede a generar la imagen docker %s", docker_image_name)
        docker_utils.build_image(image_name=docker_image_name, path=unzip_path, buildargs=build_args)
        logger.info("Imagen docker %s generada!", docker_image_name)
        # Eliminamos los datos descomprimidos
        if unzip_path:
            shutil.rmtree(unzip_path, ignore_errors=True)

    data = {'container_status': 'ok'}
    if request.method == 'POST':
        logger.debug("Petición de generacion de contenedor")
        try:
            game_id = request.session.get('game_id', None)
            group_id = request.session.get('group_id', None)
            group_game_case_id = request.POST.get("group_game_case_id", None)
            case_id = request.POST.get("case_id", None)
            ggc=GroupGameCase.objects.get(id=group_game_case_id)
            # Si es la primera vez que se inicia el caso se genera el contenedor para el player_group
            #if 0 > int(group_game_case_id):
            if not ggc.docker_container_name:
                logger.debug("Es nuevo, generamos contenedor")
                game = Game.objects.get(id=game_id)
                group = Group.objects.get(id=group_id)
                case = Case.objects.get(id=case_id)
                # El id del caso viene en negativo como clave del group game case
                logger.debug("Se va a generar el contenedor para el caso %s del ggc %s", case_id, group_game_case_id)
                if case.terminal_username:
                    username = case.terminal_username
                else:
                    username = group.name
                password = _generate_container_user_passwd(username=username)

                # Generamos el nombre de la imagen
                docker_image_name = str(game.id) + "/" + str(case.id) + "/" + str(group.id)

                # Si se quiere que el contenedor tenga el mismo nombre que la imagen
                # se deberá cambiar el valor en el settings
                docker_container_name = ''
                if settings.DOCKER_CONTAINER_NAME_EQUALS_IMAGE:
                    docker_container_name = docker_image_name

                # Comprobamos que no exista realmente un registro
                ggc = GroupGameCase.objects.filter(case_id=case_id, game_id=game_id, group_id=group_id)
                if ggc:
                    group_game_case = ggc[0]
                    #actualizamos el elemento
                    group_game_case.docker_image_name=docker_image_name
                    group_game_case.docker_container_name=docker_container_name
                    group_game_case.username=username
                    group_game_case.password=password
                    group_game_case.save()
                else:
                    # Creamos el GroupGameCase.
                    group_game_case = GroupGameCase.objects.create(case=case, game=game, group=group,
                                                                   docker_image_name=docker_image_name,
                                                                   docker_container_name=docker_container_name,
                                                                   username=username, password=password,
                                                                   protocol=case.protocol)

                    # Generamos los datos del GroupEvent
                GroupEventBusiness.generate_data(group_game_case=group_game_case)

                    # Generamos los datos del GroupArtifactInfo
                GroupArtifactInfoBusiness.generate_data(group_game_case=group_game_case, username=username)

                    # Activamos las pruebas del evento inicial
                GroupEventBusiness.activate_initial_event(group_game_case_id=group_game_case.id)

                group_game_case_id = group_game_case.id
                request.session['group_game_case_id'] = group_game_case_id

                # Generamos la imagen para el grupo
                _generate_case_container(docker_image_name=docker_image_name, case=case, username=username,
                                         password=password, group_game_case_id=group_game_case.id)

            data['case_id'] = case_id
            data['group_game_case_id'] = group_game_case_id
            data['container_status']='ok'
        except Exception as e:
            logger.error(e)
            data = {'container_status': 'error'}

    return JsonResponse(data)


@login_required(login_url='/accounts/login/')
@xframe_options_sameorigin
@require_POST
def get_story_message(request):
    data = {'status': 'error'}
    if request.method == 'POST':

        case_id = request.POST.get("case_id", None)
        story_id = request.POST.get('story_id', None)

        # Si llega el story_id se debe cargar directamente
        if story_id:
            story = Story.objects.get(id=story_id)
        elif case_id:
            # Si nos llega el case_id debemos cargar la story inicial del caso
            case = Case.objects.get(id=case_id)
            story = case.story

        data['is_embebed'] = False
        story_messages = Message.objects.filter(story_id=story.id).order_by('order')
        if story.story_type.name == StoryTypeEnum.PDF.value:
            data['show_popup'] = True
            data['is_embebed'] = True
            data['message_type']=StoryTypeEnum.PDF.value
            # Si es un pdf solo deberia haber un registro para ese story
            data['message_url'] = request.build_absolute_uri('/')+story_messages[0].file_path.url[1:]
        elif story.story_type.name == StoryTypeEnum.AUDIO.value:
            data['show_popup'] = True
            data['is_embebed'] = True
            data['message_type']=StoryTypeEnum.AUDIO.value
            data['message_url'] = story_messages[0].file_path.url
        elif story.story_type.name == StoryTypeEnum.MOVIE.value :
            data['show_popup'] = True
            data['is_embebed'] = True
            data['message_type']=StoryTypeEnum.MOVIE.value
            data['message_url'] = story_messages[0].file_path.url
        elif story.story_type.name == StoryTypeEnum.HTML.value:
            data['show_popup'] = True
            data['is_embebed'] = True
            data['message_type']=StoryTypeEnum.HTML.value
            data['story_text']=story_messages[0].plane_text
        elif story.story_type.name == StoryTypeEnum.CHAT.value:
            data['show_chat'] = True
            msgs = list()
            for msg in story_messages:
                msgs.append({'id': msg.id, 'delay': msg.delay_to_show * 1000})  # Pasamos a milisegundos
            data['chat_messages'] = msgs

        data['status'] = 'ok'

    return JsonResponse(data)


@login_required(login_url='/accounts/login/')
@require_POST
def unlock_events(request):
    data = {'status': 'error'}
    if request.method == 'POST':
        event_id = request.POST.get('event', None)
        group_game_case_id = request.session.get('group_game_case_id', None)
        if not event_id or not group_game_case_id:
            logger.error("No se presenta event_id (%s) o ggc_id (%s)", event_id, group_game_case_id)

        else:
            # Corroboramos contra bbdd que el evento que llega ha sido finalizado por el jugador
            event_finished = GroupEventBusiness.is_finished(group_game_case_id=group_game_case_id, event_id=event_id)

            if not event_finished:
                logger.error(
                    "Se ha intentado desbloquear eventos cuando el actual no habia sido superado. "
                    "(event_id:%s\tggc_id:%s)", event_id, group_game_case_id)
            else:
                # Buscamos todos aquellos eventos que tengan como predecesor el actual y los desbloqueamos
                next_group_events = GroupEventBusiness.get_and_unlock_next_events(group_game_case_id=group_game_case_id,
                                                                                  event_finished_id=event_id)

                data['status'] = 'ok'
                if next_group_events:
                    data['next_events'] = _generate_intro_event_message_data(next_group_events)
                else:
                    # Si no hemos encontrado eventos que desbloquear es porque se ha finalizado el juego
                    # Actualizamos la fecha de finalización del caso y mostramos mensaje de finalización
                    ggc = GroupGameCaseBusiness.case_finished(group_game_case_id=group_game_case_id)
                    data['game_msg'] = render(request, 'case_finished_dialog.html', {'ggc': ggc}).content.decode(
                        'utf-8')
                    # Paramos el contenedor
                    _stop_docker_container(group_game_case_id=group_game_case_id)

    if data['status'] != 'ok':
        messages.error(request, _("Se ha producido un error al desbloquear la siguiente misión."))

    return JsonResponse(data)


def _generate_intro_event_message_data(group_events):
    intro_stories_events = list()
    for group_event in group_events:
        ev = {}
        intro_stories_events.append(ev)
        event = group_event.event
        ev['case_id'] = event.case.id
        ev['story_id'] = None
        if event.event_intro_story:
            ev['story_id'] = event.event_intro_story.id

        ev['delay'] = event.delay_start * 1000  # pasamos a milisegundos
        ev['group_game_case_id'] = group_event.group_game_case.id

    return intro_stories_events


@login_required(login_url='/accounts/login/')
@require_POST
def get_current_events_messages(request):
    data = {'status': 'error'}
    if request.method == 'POST':
        group_game_case_id = request.session.get('group_game_case_id', None)
        group_events = GroupEventBusiness.get_active_events(group_game_case_id=group_game_case_id)

        data['events'] = _generate_intro_event_message_data(group_events)
        data['status'] = 'ok'

    return JsonResponse(data)


@login_required(login_url='/accounts/login/')
@require_POST
def add_messages_to_view(request):
    if request.method == 'POST':
        level = request.POST.get('level', None)
        msg = request.POST.get('message', None)
        if level and msg:
            if level.lower() == 'info':
                level = messages.INFO
            elif level.lower() == 'error':
                level = messages.ERROR
            elif level.lower() == 'warning':
                level = messages.WARNING
            elif level.lower() == 'success':
                level = messages.SUCCESS
            else:
                level = messages.DEBUG

            messages.add_message(request, level=level, message=msg)
    return render(request, "messages.html", {})


@login_required(login_url='/accounts/login/')
def get_case_title(request):
    data = {'status': 'error'}
    case_id = request.POST.get('case_id', None)
    case = Case.objects.get(id=case_id)
    if case:
        data['status'] = 'ok'
        data['title'] = case.name

    return JsonResponse(data)


@login_required(login_url='/accounts/login/')
@require_POST
def send_chat_message(request):
    data = {'status': 'error'}
    msg = request.POST.get('msg', None)
    group_game_case_id = request.session.get('group_game_case_id', None)
    conversation_id = request.POST.get('conversation_id', None)
    if msg and group_game_case_id and conversation_id:
        # Damos de alta el mensaje del usuario [Esto tiene que estar en otra petición post]
        if Conversation.objects.filter(id=conversation_id, group_game_case_id=group_game_case_id).exists():
            chat_msg = ChatMessage.objects.create(conversation_id=conversation_id, text_message=msg,
                                                  unread_message=False, is_bot_message=False)
            data['status'] = 'ok'
            data['msgid'] = chat_msg.id

    return JsonResponse(data)


@login_required(login_url='/accounts/login/')
@require_POST
def validate_chat_message(request):
    data = {'status': 'error'}
    group_game_case_id = request.session.get('group_game_case_id', None)
    chat_message_id = request.POST.get('chat_message_id', None)
    if chat_message_id and group_game_case_id:
        chat_message = ChatMessage.objects.get(id=chat_message_id)
        contact = chat_message.conversation.contact
        key_code = chat_message.text_message
        try:
            info_key = uuid.UUID(str(key_code))
        except (AttributeError, ValueError):
            info_key = str(key_code)

        if info_key and contact.is_online:
            # Validamos que la respuesta sea un codigo valido y que ademas sea valido para este evento en concreto de chat
            db_group_artifact_info = GroupArtifactInfoBusiness.validate_key_info(group_game_case_id=group_game_case_id,
                                                                                 info_key=info_key)
            msg_response = 'Eso no es lo que te he pedido'
            valid_group_artifact_info = None
            if db_group_artifact_info:
                for group_artifact_info in db_group_artifact_info:
                    event = group_artifact_info.group_event.event
                    if not event.event_intro_story or event.event_intro_story.story_type.name == StoryTypeEnum.CHAT.value:
                        if group_artifact_info.group_event.event.event_intro_story.message_set.filter(
                                character_id=contact.character_id).exists():
                            valid_group_artifact_info = group_artifact_info
                            break

            if valid_group_artifact_info and valid_group_artifact_info.is_artifact_active:
                # Validamos que la respuesta no se hubiese dado antes
                has_response = GroupResponseBusiness.has_response(group_game_case_id=group_game_case_id,
                                                                  group_artifact_info_id=db_group_artifact_info[
                                                                      0].id)
                if not has_response:
                    msg_response = None

            if msg_response:
                # Si no es valido el personaje tendrá que indicarlo dandose de alta el mensaje en bbdd y recargando el chat
                ChatMessage.objects.create(conversation=chat_message.conversation, text_message=msg_response)
            else:
                data['status'] = 'ok'
                data['group_artifact_info_id'] = valid_group_artifact_info.id
                data['artifact_name'] = valid_group_artifact_info.artifact.name
                data['key_code'] = str(valid_group_artifact_info.info_key)
                data['score'] = valid_group_artifact_info.hidden_info.score

    return JsonResponse(data)


@login_required(login_url='/accounts/login/')
@require_GET
def get_unread_message(request):
    data = {'status': 'error'}
    group_game_case_id = request.session.get('group_game_case_id', None)
    if group_game_case_id:
        if GroupGameCase.objects.filter(id=group_game_case_id).exists():
            conversations = Conversation.objects.filter(group_game_case_id=group_game_case_id)
            total_unread_msg = 0
            if conversations:
                unread_by_contact = list()
                for conversation in conversations:
                    unread_msg = conversation.chatmessage_set.filter(unread_message=True).count()
                    unread_by_contact.append({'contact_id': conversation.contact_id, 'unread_msg': unread_msg})
                    total_unread_msg += unread_msg
                data['unread_msg_by_contacts'] = unread_by_contact
            data['status'] = 'ok'
            data['total_unread_msg'] = total_unread_msg

    return JsonResponse(data)


@login_required(login_url='/accounts/login/')
@require_POST
def mark_as_read_chat_message(request):
    data = {'status': 'error'}
    group_game_case_id = request.session.get('group_game_case_id', None)
    contact_id = request.POST.get('contact_id', None)
    if group_game_case_id and contact_id:
        if GroupGameCase.objects.filter(id=group_game_case_id).exists():
            conversation = Conversation.objects.filter(group_game_case_id=group_game_case_id, contact_id=contact_id)
            if conversation:
                _mark_as_read(conversation[0])

            data['status'] = 'ok'

    return JsonResponse(data)


def _mark_as_read(conversation_id):
    ChatMessage.objects.filter(conversation_id=conversation_id).update(unread_message=False)


@login_required(login_url='/accounts/login/')
@require_GET
def download_clue(request, artifact_id=None):
    ggc_id = request.session.get('group_game_case_id', None)
    if artifact_id and ggc_id:
        group_artifact_info = GroupArtifactInfo.objects.filter(artifact_id=artifact_id, group_game_case_id=ggc_id)
        if group_artifact_info:
            # Un artefacto puede tener multiples informaciones ocultas, por eso la query anterior puede
            # devolver más registros.
            group_artifact_info = group_artifact_info[0]
            download_path = os.path.join(settings.MEDIA_ROOT, 'clues')
            try:  # Intentamos generar los directorios que falten
                os.makedirs(download_path)
            except Exception as e:
                pass
            artifact = os.path.join(download_path,
                                    "{}_{}".format(group_artifact_info.artifact_id, group_artifact_info.artifact.name))
            # recuperamos el fichero y lo almacenamos en el servidor
            try:
                docker_utils.download_file_from_container(group_artifact_info=group_artifact_info, temp_dir=artifact)
                # servimos el fichero
                return FileResponse(open(artifact, 'rb'), filename=group_artifact_info.artifact.name,
                                    as_attachment=True)
            except Exception as e:
                logger.error(e)
                return render(request, '404.html', {})

    # Si llegamos hasta aqui es que no ha sido posible recuperar el fichero
    return render(request, '404.html', {})


@login_required(login_url='/accounts/login/')
@user_with_game_and_case_permission
def case_detail(request, case_id=None, group_id=None):
    logger.info("Pantalla de detalle de caso %s", case_id)

    title = ''
    items = None
    if group_id:
        group = Group.objects.filter(id=group_id, course__game__case__id=case_id)
        if not group:
            logger.error("El grupo %s no tiene el caso %s", group_id, case_id)
            messages.error(request, _("El caso no esta asignado al usuario indicado."))
            return redirect('home')
        else:
            group = group[0]
            case = Case.objects.filter(id=case_id)
            if not case:
                logger.error("Caso %s no encontrado.", case_id)
                messages.error(request, _("Caso %s no encontrado." % case_id))
                return redirect('home')
            else:
                case = case[0]

            # Recuperamos los Group_events para group_id parametrizado
            group_events = GroupEventBusiness.get_gevents_from_case_and_group(case_id=case_id, group_id=group_id)

            # Si el group_id NO pertenece al usuario que consulta tenemos que ofuscar nombre de eventos y
            # la info encontrada de todos aquellos eventos que el usuario no haya superado
            groups = GroupBusiness.get_by_course_and_user(course_id=case.game.course_id, user_id=request.user.id)

            is_my_group = groups and groups.filter(id=group_id).exists() or request.user.is_staff
            user_gevents = list()
            if not is_my_group:
                # Recuperamos los id de los eventos que tiene el usuario que hace la consulta
                user_group_events = GroupEventBusiness.get_gevents_from_case_and_user(case_id=case_id,
                                                                                      user_id=request.user.id)
                if user_group_events:
                    for ge in user_group_events:
                        user_gevents.append(ge.event_id)

            paginator = Paginator(group_events, 10)
            page = request.GET.get('page')
            items = paginator.get_page(page)

            title = _('Estado del caso {} para el usuario {}'.format(case.name, group.name))

    return render(request, 'case_detail.html', {'items': items,
                                                'is_my_group': is_my_group,
                                                'case': case,
                                                'group': group,
                                                'user_gevents': user_gevents})


@login_required(login_url='/accounts/login/')
@user_with_event_permission
def event_detail(request, event_id=None, group_id=None):
    logger.info("Pantalla de detalle del evento %s", event_id)
    title = ''
    items = None
    if group_id:
        group = Group.objects.filter(id=group_id, groupgamecase__groupevent__event_id=event_id)
        if not group:
            logger.error("El grupo %s no tiene el evento %s", group_id, event_id)
            messages.error(request, _("La misión no esta asignada al usuario indicado."))
            return redirect('home')
        else:
            group = group[0]
            event = Event.objects.filter(id=event_id)
            if not event:
                logger.error("Evento %s no encontrado.", event_id)
                messages.error(request, _("Misión no encontrada."))
                return redirect('home')
            else:
                event = event[0]

            # Recuperamos los Group_response para group_id parametrizado
            group_artifact_infos = GroupArtifactInfoBusiness.get_by_event_and_group(event_id=event_id,
                                                                                    group_id=group_id)

            # Si el group_id NO pertenece al usuario que consulta tenemos que ofuscar la info encontrada
            # que el usuario no haya superado
            groups = GroupBusiness.get_by_course_and_user(course_id=event.case.game.course_id, user_id=request.user.id)
            is_my_event = groups and groups.filter(id=group_id).exists() or request.user.is_staff
            user_hidden_infos = list()
            if not is_my_event:
                # Recuperamos los id de los artifact_info que tiene el usuario que hace la consulta
                user_gartifact_infos = GroupArtifactInfoBusiness.get_by_event_and_user(event_id=event_id,
                                                                                       user_id=request.user.id)
                if user_gartifact_infos:
                    for infos in user_gartifact_infos:
                        user_hidden_infos.append(infos.hidden_info_id)

            paginator = Paginator(group_artifact_infos, 10)
            page = request.GET.get('page')
            items = paginator.get_page(page)

    return render(request, 'event_detail.html', {'items': items,
                                                 'event': event,
                                                 'group': group,
                                                 'is_my_event': is_my_event,
                                                 'user_hidden_infos': user_hidden_infos})


@login_required(login_url='/accounts/login/')
@user_with_event_permission
@require_POST
def response_player_like(request, event_id=None, group_id=None):
    data = {'status': 'error'}
    group_artifact_info_id = request.POST.get('group_artifact_info_id', None)
    if group_artifact_info_id:
        event = Event.objects.get(id=event_id)
        user_id = request.user.id
        user_groups = GroupBusiness.get_by_course_and_user(course_id=event.case.game.course_id, user_id=user_id)
        # No permitimos sumar un like del propio usuario
        if user_groups.exists() and not user_groups.filter(id=group_id).exists():
            PlayerRatingBusiness.toggle_player_rating(group_artifact_info_id=group_artifact_info_id,
                                                      user_id=user_id, score=1)
            data['status'] = 'ok'
    return JsonResponse(data)
