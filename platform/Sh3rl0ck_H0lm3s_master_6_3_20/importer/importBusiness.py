import logging
import os
from shutil import copy2 as copy

from django.utils import timezone
from django.db import IntegrityError
from django.utils.translation import gettext_lazy as _

from Sh3rl0ck_H0lm3s.settings import MEDIA_ROOT
from player.models import Department, Course
from game.models import StoryType, \
    Tool, \
    ToolParameter, \
    Story, \
    Message, \
    Artifact, \
    ArtifactType, \
    HiddenInfo, \
    HidingType, \
    ToolParameterValue, \
    Game, \
    Case, \
    Course, \
    Event, \
    Character

logger = logging.getLogger(__name__)

# creamos las instancias para los recursos estaticos del juego
COURSES_RESOURCES_PATH = 'courses'
GAME_RESOURCES_PATH = 'games'
CASE_RESOURCES_PATH = 'cases'
CHARACTER_RESOURCES_PATH = 'characters'
MESSAGE_RESOURCES_PATH = 'messages'


def _copy_resource(src_path, import_path, dst_relative_path):
    # Obtenemos el nombre del fichero
    filename = os.path.basename(src_path)

    # Eliminamos la barra inicial si la tuviese
    if src_path.startswith('/') or src_path.startswith('\\'):
        src_path = src_path[1:]

    # Completamos el path del fichero
    src_path = os.path.join(import_path, src_path)

    # Generamos url para acceder al recurso desde el aplicativo
    server_resource_path = os.path.join(dst_relative_path, filename)

    # Generamos la ruta de destino donde se alojará el fichero
    dst_path = os.path.join(MEDIA_ROOT, server_resource_path)
    try:  # Intentamos generar los directorios que falten
        os.makedirs(os.path.dirname(dst_path))
    except Exception as e:
        pass

    # Copiamos el recurso al destino
    copy(src_path, dst_path)

    # Devolvemos la url para guardarla en base de datos
    return server_resource_path


class ImportBusiness:
    @staticmethod
    def insert_story_type(story_type, import_path=None):
        story_type_id = story_type.storyTypeId
        name = story_type.name
        description = story_type.description
        return StoryType.objects.create(id=story_type_id,
                                        name=name,
                                        description=description)

    @staticmethod
    def insert_character(character, import_path=None):
        name = character.name
        full_name = character.full_name
        mail_address = character.mail_address

        db_character = Character.objects.filter(full_name=full_name)
        if db_character:
            return db_character[0]
        else:
            return Character.objects.create(name=name,
                                            full_name=full_name,
                                            mail_address=mail_address)

    @staticmethod
    def complete_character(character, game_id, case_id, import_path):
        avatar = character.avatar_path
        full_name = character.full_name

        db_character = Character.objects.filter(full_name=full_name)
        if db_character:
            django_character = db_character[0]
            django_character.case_id = case_id
            # copiamos el recurso de la foto del caso en el servidor
            dst_relative_path = os.path.join(GAME_RESOURCES_PATH,
                                             str(game_id),
                                             CASE_RESOURCES_PATH,
                                             str(case_id),
                                             CHARACTER_RESOURCES_PATH)
            if avatar:
                django_character.avatar = _copy_resource(avatar, import_path, dst_relative_path)
            django_character.save()
            return django_character

    @staticmethod
    def insert_tools(tool, import_path=None):
        tools = tool.get_tool()
        for xml_tool in tools:
            ImportBusiness.insert_tool(xml_tool, import_path)

    @staticmethod
    def insert_tool(tool, import_path=None):
        name = tool.name
        description = tool.description
        command = tool.command
        hiding_types = tool.get_hiding_type()
        parameters = tool.get_parameter()

        # Comprobamos si la herramienta ya existia para el mismo nombre y comando. Si ya existe no la damos de alta
        django_tool = Tool.objects.filter(name=name, command=command)
        if django_tool:
            django_tool = django_tool[0]
        else:
            django_tool = Tool.objects.create(name=name,
                                              description=description,
                                              command=command)
        tool_id = django_tool.id
        if hiding_types:
            for hiding_type in hiding_types:
                hiding_type_name = hiding_type.name
                hiding_type_description = hiding_type.description
                db_hiding_type = HidingType.objects.filter(name=hiding_type_name)
                if db_hiding_type:
                    # Si ya existe el tipo verificamos que es para la misma herramienta, sino mostramos un error
                    # dado que por modelo no puede haber 2 herramientas para un mismo tipo
                    if db_hiding_type[0].tool_id != tool_id:
                        logger.error(
                            "Se intenta dar de alta herramienta %s con hiding_type %s cuando esta ya existe para otra herramienta",
                            tool, hiding_type_name)
                        raise IntegrityError(_(
                            'HidingType ya existe y está asignado para la herramienta %s' % db_hiding_type[
                                0].tool.name))
                else:
                    # Damos de alta el tipo
                    HidingType.objects.create(name=hiding_type_name, description=hiding_type_description,
                                              tool_id=tool_id)
        for param in parameters:
            name = param.name
            description = param.description
            parameter = param.parameter

            # Comprobamos si ya existe un parametro con el mismo nombre para la herramienta
            if not ToolParameter.objects.filter(name=name, tool_id=tool_id).exists():
                ToolParameter.objects.create(name=name,
                                             description=description,
                                             parameter=parameter,
                                             tool_id=tool_id)
        return django_tool

    @staticmethod
    def insert_story(story, import_path=None, game_id=None, case_id=None, insert_message=True, characters_map=None,
                     characters=None):
        name = story.name
        description = story.description
        story_type_id = story.story_type_id
        messages = story.get_message()

        django_story = Story.objects.create(name=name,
                                            description=description,
                                            story_type_id=story_type_id)

        if insert_message:
            for msg in messages:
                if characters_map and msg.character_key:
                    db_character = characters_map[msg.character_key]
                    if db_character:
                        characters.add(db_character)
                ImportBusiness.insert_message(msg, import_path=import_path, story_id=django_story.id, game_id=game_id,
                                              case_id=case_id, characters_map=characters_map)

        return django_story

    @staticmethod
    def insert_message(message, import_path=None, story_id=None, game_id=None, case_id=None, characters_map=None):
        if not story_id:
            logger.error("En el alta de message no se ha especificado el story_id")

        plane_text = message.plane_text
        delay_to_show = message.delay_to_show
        order = message.order

        character = None
        if message.character_key and characters_map:
            character = characters_map[message.character_key]

        django_msg = Message.objects.create(plane_text=plane_text,
                                            delay_to_show=delay_to_show,
                                            order=order,
                                            story_id=story_id,
                                            character=character)

        if game_id and case_id and message.file_path:
            ImportBusiness._copy_story_messages_resources(django_msg, message.file_path, import_path, game_id, case_id)

    @staticmethod
    def _copy_story_messages_resources(django_msg, file_path, import_path, game_id=None, case_id=None):
        dst_relative_path = os.path.join(GAME_RESOURCES_PATH,
                                         str(game_id),
                                         CASE_RESOURCES_PATH,
                                         str(case_id),
                                         MESSAGE_RESOURCES_PATH)

        # copiamos el recurso en el servidor y guardamos la url en bbdd
        django_msg.file_path = _copy_resource(file_path, import_path, dst_relative_path)
        django_msg.save()

    @staticmethod
    def insert_artifact_type(artifact_type, import_path=None):
        name = artifact_type.name
        description = artifact_type.description

        # Comprobamos primero si existe un tipo con el mismo nombre
        django_artifact_type = ArtifactType.objects.filter(name=name)
        if django_artifact_type.exists():
            return django_artifact_type[0]
        else:
            return ArtifactType.objects.create(name=name,
                                               description=description)

    @staticmethod
    def insert_artifact(artifact, import_path=None, event_map=None):
        name = artifact.name
        description = artifact.description
        path = artifact.path
        hidden_infos = artifact.get_hidden_info()
        case_id = artifact.case_id
        artifact_type = artifact.get_artifact_type()

        case = Case.objects.filter(id=case_id)

        django_artifact_type = ImportBusiness.insert_artifact_type(artifact_type)

        django_artifact = Artifact.objects.create(name=name,
                                                  description=description,
                                                  case=case[0],
                                                  artifact_type_id=django_artifact_type.id,
                                                  path=path)

        if hidden_infos:
            for hidden_info in hidden_infos:
                django_event = event_map[hidden_info.event_key]
                ImportBusiness.insert_hidden_info(hidden_info=hidden_info, django_event=django_event,
                                                  artifact_id=django_artifact.id)

        return django_artifact

    @staticmethod
    def insert_hiding_type(hiding_type, import_path=None):
        name = hiding_type.name
        description = hiding_type.description
        tool_id = hiding_type.tool_id

        tool = Tool.objects.filter(id=tool_id)
        if not tool:
            raise IntegrityError(_('No se ha encontrado ninguna herramienta con id %d' % tool_id))

        return HidingType.objects.create(name=name,
                                         description=description,
                                         tool=tool[0])

    @staticmethod
    def insert_hidden_info(hidden_info, django_event, artifact_id, import_path=None):
        name = hidden_info.name
        description = hidden_info.description
        score = hidden_info.score
        hiding_type_id = hidden_info.hiding_type_id
        tool_param_values = hidden_info.get_toolParamValue()
        is_event_key_info = hidden_info.is_event_key_info
        common_key_code = hidden_info.common_key_code
        prefix_key_code = hidden_info.prefix_key_code
        suffix_key_code = hidden_info.suffix_key_code
        random_key_code_word = False
        random_word_maxlength = 0

        if hidden_info.random_key_code_word:
            random_word_maxlength = 9
            random_key_code_word = True
            if hidden_info.random_word_maxlength:
                random_word_maxlength = hidden_info.random_word_maxlength

        hiding_type = HidingType.objects.filter(id=hiding_type_id)
        if not hiding_type:
            raise IntegrityError(_('No se ha encontrado ningun hidingType con id %d' % hiding_type_id))

        artifact = Artifact.objects.filter(id=artifact_id)

        django_hiding_info = HiddenInfo.objects.create(name=name,
                                                       description=description,
                                                       event=django_event,
                                                       score=score,
                                                       artifact_id=artifact[0].id,
                                                       hiding_type_id=hiding_type[0].id,
                                                       is_event_key=is_event_key_info,
                                                       common_key_code=common_key_code,
                                                       prefix_key_code=prefix_key_code,
                                                       suffix_key_code=suffix_key_code,
                                                       random_key_code_word=random_key_code_word,
                                                       random_word_maxlength=random_word_maxlength)

        if tool_param_values:
            order = 0
            for tool_param_value in tool_param_values:
                order += 1
                tool_param_value.hidden_info_id = django_hiding_info.id
                ImportBusiness.insert_tool_param_value(tool_param_value=tool_param_value, order=order)
        return django_hiding_info

    @staticmethod
    def insert_tool_param_value(tool_param_value, order, import_path=None):
        param_id = tool_param_value.param_id
        tool_id = tool_param_value.tool_id
        hidden_info_id = tool_param_value.hidden_info_id
        value = tool_param_value.value
        add_key_code = tool_param_value.add_key_code

        return ToolParameterValue.objects.create(param_id=param_id,
                                                 tool_id=tool_id,
                                                 hidden_info_id=hidden_info_id,
                                                 value=value,
                                                 add_key_code=add_key_code,
                                                 order=order)

    @staticmethod
    def insert_case(case, import_path=None, game_id=None):
        game_id = case.game_id
        story = case.story
        name = case.name
        description = case.description
        published_date = case.published_date
        is_published = case.is_published
        base_img_path = case.base_img_path
        events = case.get_event()
        case_image_path = case.case_image
        artifacts = case.get_artifact()
        protocol = case.protocol
        terminal_username = case.terminal_username

        # Damos soporte timezone a las fechas nativas
        if is_published:
            if published_date:
                published_date = timezone.make_aware(published_date, timezone.get_current_timezone())
            else:
                published_date = timezone.now()
        else:
            published_date = None

        # Damos de alta los personajes del caso
        characters_map = {}
        if case.get_character:
            for character in case.get_character():
                django_character = ImportBusiness.insert_character(character=character, import_path=import_path)
                characters_map[character.character_key] = django_character

        characters = set()
        # Damos de alta la historia
        django_story = ImportBusiness.insert_story(story, import_path=import_path, game_id=game_id,
                                                   insert_message=False, characters_map=characters_map,
                                                   characters=characters)

        # Buscamos el juego
        django_game = Game.objects.filter(id=game_id)
        if not django_game:
            raise IntegrityError(_('No se ha encontrado ningún juego con id %d' % game_id))

        # Damos de alta el caso
        django_case = Case.objects.create(game=django_game[0],
                                          story=django_story,
                                          name=name,
                                          description=description,
                                          published_date=published_date,
                                          is_published=is_published,
                                          protocol=protocol,
                                          terminal_username=terminal_username)

        # Añadimos el case_id a los personajes y copiamos su avatar
        if characters_map:
            for data_character in case.get_character():
                ImportBusiness.complete_character(character=data_character, game_id=game_id, case_id=django_case.id,
                                                  import_path=import_path)

        # Copiamos los messages del story del case
        messages = story.get_message()
        for msg in messages:
            ImportBusiness.insert_message(msg, import_path=import_path, story_id=django_story.id, game_id=game_id,
                                          case_id=django_case.id, characters_map=characters_map)

        # copiamos el recurso de la foto del caso en el servidor
        dst_relative_path = os.path.join(GAME_RESOURCES_PATH,
                                         str(django_game[0].id),
                                         CASE_RESOURCES_PATH,
                                         str(django_case.id))

        django_case.case_image = _copy_resource(case_image_path, import_path, dst_relative_path)

        # copiamos el recurso de la imagen base del caso en el servidor
        django_case.base_img_path = _copy_resource(base_img_path, import_path, dst_relative_path)

        django_case.save()

        if events:
            event_map = {}
            for event in events:
                event.case_id = django_case.id
                event_key = event.event_key
                previous_event_id = event.previous_event_id
                previous_event_key = event.previous_event_key
                if previous_event_id:
                    event.previous_event_id = previous_event_id
                elif previous_event_key:
                    django_event = event_map.get(previous_event_key, None)
                    if django_event:
                        event.previous_event_id = django_event.id

                django_event = ImportBusiness.insert_event(event, import_path=import_path, game_id=game_id,
                                                           characters_map=characters_map)
                if event_key:
                    event_map[event_key] = django_event

        # damos de alta los artefactos
        if artifacts:
            for artifact in artifacts:
                artifact.case_id = django_case.id
                ImportBusiness.insert_artifact(artifact, event_map=event_map)

        return django_case

    @staticmethod
    def insert_game(game, import_path=None):
        course_id = game.course_id
        name = game.name
        description = game.description
        published_date = game.published_date
        is_published = game.is_published
        src_game_image_path = game.game_image
        cases = game.get_case()

        # Damos soporte timezone a las fechas nativas
        if is_published:
            if published_date:
                published_date = timezone.make_aware(published_date, timezone.get_current_timezone())
            else:
                published_date = timezone.now()
        else:
            published_date = None

        # Buscamos la asignatura
        django_course = Course.objects.filter(id=course_id)
        if not django_course:
            raise IntegrityError(_('No se ha encontrado ninguna asignatura con id %d' % course_id))

        # Comprobamos si existe el juego o si tenemos que darlo de alta
        django_game = Game.objects.filter(name=name, course_id=course_id)
        if django_game:
            django_game = django_game[0]
            # Si ya existe el juego verificamos si tenemos que cambiar el estado a publicado
            if is_published and not django_game.is_published:
                django_game.is_published = is_published
                django_game.published_date = published_date
                django_game.save()
        else:
            # Damos de alta el juego
            django_game = Game.objects.create(course=django_course[0],
                                              name=name,
                                              description=description,
                                              published_date=published_date,
                                              is_published=is_published)
            # Solo añadimos la imagen del juego si este es nuevo
            dst_relative_path = os.path.join(GAME_RESOURCES_PATH, str(django_game.id))
            # copiamos el recurso en el servidor y guardamos la url en bbdd
            django_game.game_image = _copy_resource(src_game_image_path, import_path, dst_relative_path)
            django_game.save()

        # Damos de alta los casos
        if cases:
            for case in cases:
                case.game_id = django_game.id
                ImportBusiness.insert_case(case=case, import_path=import_path)

        return django_game

    @staticmethod
    def insert_event(event, import_path=None, game_id=None, characters_map=None):
        case_id = event.case_id
        event_intro_story = event.event_intro_story
        event_end_story = event.event_end_story
        previous_event_id = event.previous_event_id
        name = event.name
        description = event.description
        delay_start = event.delay_start
        onfinish_cancel_active_events = event.onfinish_cancel_active_events

        characters = set()
        django_event_intro_story = None
        if event_intro_story:
            django_event_intro_story = ImportBusiness.insert_story(event_intro_story, import_path, game_id=game_id,
                                                                   case_id=case_id, characters_map=characters_map,
                                                                   characters=characters)

        django_event_end_story = None
        if event_end_story:
            django_event_end_story = ImportBusiness.insert_story(event_end_story, import_path, game_id=game_id,
                                                                 case_id=case_id, characters_map=characters_map,
                                                                 characters=characters)

        django_previous_event = None
        if previous_event_id:
            tmp = Event.objects.filter(id=previous_event_id)
            if tmp:
                django_previous_event = tmp[0]
        # Recuperamos el caso
        django_case = Case.objects.filter(id=case_id)

        django_event = Event.objects.create(case=django_case[0],
                                            event_intro_story=django_event_intro_story,
                                            event_end_story=django_event_end_story,
                                            previous_event=django_previous_event,
                                            name=name,
                                            description=description,
                                            delay_start=delay_start,
                                            onfinish_cancel_active_events=onfinish_cancel_active_events)

        if characters:
            # Añadimos al evento los personajes
            for character in characters:
                django_event.characters.add(character)

        return django_event

    @staticmethod
    def insert_department(department, import_path=None):
        name = department.name
        url = department.url

        courses = department.get_course()

        # Comprobamos si existe el departamento o si tenemos que darlo de alta
        django_department = Department.objects.filter(name=name)
        if django_department:
            django_department = django_department[0]
        else:
            # Damos de alta el departamento
            django_department = Department.objects.create(name=name, url=url)

        # Damos de alta las asignaturas
        if courses:
            for course in courses:
                ImportBusiness.insert_course(course=course, department_id=django_department.id, import_path=import_path)

        return django_department

    @staticmethod
    def insert_course(course, department_id, import_path=None):
        name = course.name
        acronym = course.acronym
        course_image_path = course.course_image

        # Comprobamos si existe la asignatura o si tenemos que darla de alta
        django_course = Course.objects.filter(name=name)
        if django_course:
            django_course = django_course[0]
            # Si ya existia en bbdd pero no tenia acronimo lo actualizamos
            if not django_course.acronym and acronym:
                django_course.acronym = acronym
                django_course.save()
        else:
            # Damos de alta el departamento
            django_course = Course.objects.create(name=name, acronym=acronym, department_id=department_id)

        # copiamos el recurso de la foto del caso en el servidor
        dst_relative_path = os.path.join(COURSES_RESOURCES_PATH,
                                         str(django_course.id))

        django_course.course_image = _copy_resource(course_image_path, import_path, dst_relative_path)
        django_course.save()
        
        return django_course
