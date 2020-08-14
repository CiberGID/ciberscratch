import logging
import uuid
import math
from datetime import datetime
from django.utils import timezone
from django.db.models import Sum, Count

from .models import GroupGameCase, Group, Game,Case,HiddenInfo, GroupArtifactInfo, ToolParameterValue, GroupResponse, Event, \
    GroupEvent, Artifact, StoryTypeEnum, Contact, Conversation, Message, ChatMessage, PlayerRating, LearnActivity, User
from .utils import text_params_binding
from guacamole.utils import DOCKER_PARAM_PATTERN as PARAM_PATTERN
from codenamize import codenamize
import random

logger = logging.getLogger(__name__)


class GroupGameCaseBusiness:
    @staticmethod
    def activate_game(group_id, game_id):
        #lo primero debemos comprobar si el usuario ya está jugando este juego
        ggc=GroupGameCase.objects.filter(group=group_id,game=game_id)
        #Si no hay casos asociados de antes
        if len(ggc) == 0:
            #recuperamos los casos del juego
            casos=Case.objects.filter(game=game_id,is_published=True)
            #para cada caso tenemos que crear un GroupGameCase
            for c in casos:
                grupo=Group.objects.get(id=group_id)
                juego=Game.objects.get(id=game_id)
                nuevo_caso=GroupGameCase(group=grupo,game=juego,case=c,protocol=c.protocol)
                nuevo_caso.save()
                return True
        return False
        #sino no hacemos nada: ya estamos jugando
    @staticmethod
    def get_by_group_and_game(group_id, game_id):
        ggc=GroupGameCase.objects.filter(group=group_id,game=game_id)
        return ggc

    @staticmethod
    def get_by_group_game_and_case(group_id, game_id, case_id):
        return GroupGameCase.objects.filter(group=group_id, game=game_id, case=case_id)

    @staticmethod
    def case_finished(group_game_case_id):
        ggc = GroupGameCase.objects.filter(id=group_game_case_id)
        ggc.update(finish_date=timezone.now())
        return ggc[0]

    @staticmethod
    def get_own_cases(group_id, only_active_cases):
        return GroupGameCase.objects.filter(group_id=group_id, start_date__isnull=False,
                                            finish_date__isnull=only_active_cases)

    @staticmethod
    def update_total_score(group_game_case_id):
        total_score = GroupResponse.objects.filter(group_game_case_id=group_game_case_id).aggregate(Sum('score'))
        GroupGameCase.objects.filter(id=group_game_case_id).update(total_score=total_score['score__sum'])

    @staticmethod
    def get_case_classification(case_id):
        return GroupGameCase.objects.filter(case_id=case_id).annotate(
            responses=Count('groupresponse'), missions=Count('groupevent__finish_date')).order_by('-total_score',
                                                                                                  '-missions',
                                                                                                  '-responses')

    @staticmethod
    def count_complete_missions(group_game_case_id):
        return GroupGameCase.objects.filter(id=group_game_case_id, groupevent__finish_date__isnull=False).count()


class GroupEventBusiness:
    @staticmethod
    def generate_data(group_game_case):
        events = Event.objects.filter(case_id=group_game_case.case.id)
        items_count = 0
        for event in events:
            if len(GroupEvent.objects.filter(group_game_case=group_game_case,event=event))==0:
                GroupEvent.objects.create(group_game_case=group_game_case,
                                          event=event)
                items_count += 1

        logger.debug("Se han creado %d GroupEvent para el grupo %d", items_count, group_game_case.group.id)

    @staticmethod
    def activate(group_game_case_id, event_id=None, group_event=None):
        if not group_event:
            group_event = GroupEvent.objects.get(group_game_case_id=group_game_case_id, event_id=event_id)

        if group_event:
            group_event.start_date = timezone.now()
            group_event.is_active = True
            group_event.save()
            # Activamos los artefactos asociados a este evento
            GroupArtifactInfoBusiness.enable_by_group_event(group_event)

        # Si hay personajes de chat los añadimos a los contacto
        if group_event.event.event_intro_story_id \
                and StoryTypeEnum.CHAT.value == group_event.event.event_intro_story.story_type.name \
                or group_event.event.event_end_story_id \
                and StoryTypeEnum.CHAT.value == group_event.event.event_end_story.story_type.name:
            characters = group_event.event.characters.all()
            if characters:
                for character in characters:
                    ContactBusiness.add_contact(group_game_case_id=group_game_case_id, character=character)

    @staticmethod
    def activate_initial_event(group_game_case_id):
        group_events = GroupEvent.objects.filter(group_game_case_id=group_game_case_id,
                                                 event__previous_event__isnull=True)
        for group_event in group_events:
            GroupEventBusiness.activate(group_game_case_id=group_game_case_id, group_event=group_event)

    @staticmethod
    def check_finish_event_response(group_game_case_id, hidden_info_id):
        db_group_event = GroupEvent.objects.filter(group_game_case_id=group_game_case_id,
                                                   groupartifactinfo__hidden_info_id=hidden_info_id,
                                                   groupartifactinfo__hidden_info__is_event_key=True)

        # Si la respuesta soluciona un evento lo marcamos como completo
        group_event = None
        if db_group_event:
            # Como mucho solo deberia devolver un registro
            group_event = db_group_event[0]
            GroupEventBusiness.disable_group_event(group_event, timezone.now())

            # Si el evento tiene marcado el flag que indica que ningun evento puede seguir activo
            # a su fin procesamos dichos eventos
            if group_event.event.onfinish_cancel_active_events:
                group_events_to_cancel = GroupEvent.objects.filter(group_game_case_id=group_game_case_id,
                                                                   is_active=True)
                for group_event_cancel in group_events_to_cancel:
                    GroupEventBusiness.disable_group_event(group_event=group_event_cancel)

        return group_event

    @staticmethod
    def disable_group_event(group_event, finish_date=None):
        if finish_date:
            group_event.finish_date = finish_date
        group_event.is_active = False
        group_event.save()
        GroupArtifactInfoBusiness.disable_by_group_event(group_event=group_event)
        # Desconectamos a los personajes que ya no participen en un evento activo
        ContactBusiness.disconect_contacts(group_game_case_id=group_event.group_game_case_id, finish_date=finish_date)

    @staticmethod
    def is_finished(group_game_case_id, event_id):
        return 0 < GroupEvent.objects.filter(group_game_case_id=group_game_case_id, event_id=event_id,
                                             finish_date__isnull=False).count()

    @staticmethod
    def get_and_unlock_next_events(event_finished_id, group_game_case_id):
        group_events = GroupEvent.objects.filter(group_game_case_id=group_game_case_id,
                                                 event__previous_event_id=event_finished_id) \
            .order_by('event__delay_start')

        # Activamos los groupEvent y los groupArtifactInfo
        for group_event in group_events:
            GroupEventBusiness.activate(group_game_case_id=group_game_case_id, group_event=group_event)

        return group_events

    @staticmethod
    def get_active_events(group_game_case_id):
        return GroupEvent.objects.filter(group_game_case_id=group_game_case_id, is_active=True).order_by(
            'event__delay_start')

    @staticmethod
    def get_gevents_from_case_and_group(case_id, group_id):
        return GroupEvent.objects.filter(group_game_case__case_id=case_id, group_game_case__group_id=group_id,
                                         group_game_case__group__enabled=True, finish_date__isnull=False,
                                         is_active=False).order_by('finish_date')

    @staticmethod
    def get_gevents_from_case_and_user(case_id, user_id):
        return GroupEvent.objects.filter(group_game_case__case_id=case_id,
                                         group_game_case__group__users__exact=user_id,
                                         group_game_case__group__enabled=True, finish_date__isnull=False,
                                         is_active=False).order_by('finish_date')

    @staticmethod
    def count_hidden_info_founded(group_event_id):
        return GroupEvent.objects.filter(id=group_event_id, groupartifactinfo__groupresponse__isnull=False).count()
        # group_event.groupartifactinfo_set.filter(groupresponse__isnull=False).count()

    @staticmethod
    def sum_group_event_score(group_event_id):
        score = GroupEvent.objects.filter(id=group_event_id, groupartifactinfo__groupresponse__isnull=False).aggregate(
            Sum('groupartifactinfo__groupresponse__score'))

        if score:
            return score['groupartifactinfo__groupresponse__score__sum']
        return 0


class GroupArtifactInfoBusiness:
    @staticmethod
    def validate_key_info(group_game_case_id, info_key):
        group_artifact_info = GroupArtifactInfo.objects.filter(group_game_case_id=group_game_case_id,
                                                               info_key__contains=info_key)
        key_founds = list()
        if group_artifact_info:
            for group_ai in group_artifact_info:
                if len(group_ai.info_key) == len(str(info_key)):
                    key_founds.append(group_ai)
                elif ((group_ai.info_key.startswith("'") and group_ai.info_key.endswith("'"))
                    or (group_ai.info_key.startswith('"') and group_ai.info_key.endswith('"')))\
                        and group_ai.info_key[1:-1] == info_key:
                    key_founds.append(group_ai)

        return key_founds

    @staticmethod
    def _calc_words_count(maxlength, words_count=2):
        if 5 > maxlength or words_count > (maxlength / 2):
            return codenamize(random.randint(0, 999999999), 0, maxlength, '', True)

        remainder = maxlength % words_count
        word_len = maxlength / words_count
        if remainder == 0:
            # (bloque de palabras, cantidad de palabras, tamaño maximo, join, capitalize)
            return codenamize(random.randint(0, 999999999), words_count - 1, word_len, '', True)
        elif remainder == (words_count - 1):
            # (bloque de palabras, cantidad de palabras, tamaño maximo, join, capitalize)
            return codenamize(random.randint(0, 999999999), words_count - 1, math.trunc(word_len), '_', True)
        else:
            return GroupArtifactInfoBusiness._calc_words_count(maxlength=maxlength, words_count=words_count + 1)

    @staticmethod
    def generate_data(group_game_case, username=None):
        def _generate_info_key(hidden_info):
            if hidden_info.random_key_code_word:
                # Si se quiere un codigo que sea legible obtenemos una aleatoriamente
                word_max_length = hidden_info.random_word_maxlength
                # Si esta definido tamaño maximo de palabra la calculamos en base a el
                if hidden_info.random_word_maxlength:
                    info_key = GroupArtifactInfoBusiness._calc_words_count(
                        maxlength=word_max_length)
                    # Si la clave no llega al maximo especificado rellenamos con tantas eses que sean necesarias
                    while len(info_key) < word_max_length:
                        info_key = "{}s".format(info_key)
                else:
                    info_key = codenamize(random.randint(0, 999999999))
            else:
                # En el caso de que no se haya especificado preferencia generamos un uuid
                info_key = uuid.uuid4()
            return info_key

        username_param = {}
        if username:
            username_param['${username}'] = username
        hidden_infos = HiddenInfo.objects.filter(artifact__case_id=group_game_case.case.id)
        items_count = 0
        for hidden_info in hidden_infos:
            try:
                group_event = GroupEvent.objects.get(group_game_case_id=group_game_case, event_id=hidden_info.event.id)
                info_key = hidden_info.common_key_code
                path = hidden_info.artifact.path
                if username_param:
                    path = text_params_binding(path, username_param, pattern=PARAM_PATTERN)
                # Si tiene que llevar una clave forzada damos alta con esta, en caso contrario generamos uuid aleatorio
                if not info_key:
                    info_key = _generate_info_key(hidden_info)

                # Añadimos el prefijo si se ha especificado
                if hidden_info.prefix_key_code:
                    info_key = "{}{}".format(hidden_info.prefix_key_code, info_key)
                # Añadimos el sufijo si se ha especificado
                if hidden_info.suffix_key_code:
                    info_key = "{}{}".format(info_key, hidden_info.suffix_key_code)

                GroupArtifactInfo.objects.create(group_game_case=group_game_case,
                                                 group_event_id=group_event.id,
                                                 artifact=hidden_info.artifact,
                                                 hidden_info=hidden_info,
                                                 artifact_path=path,
                                                 info_key=info_key)
                items_count += 1
            except Exception as e:
                logger.error(e)

        logger.debug("Se han creado %d GroupArtifactInfo para el grupo %d", items_count, group_game_case.group.id)

    @staticmethod
    def enable_by_group_event(group_event):
        GroupArtifactInfo.objects.filter(group_event_id=group_event.id).update(is_artifact_active=True)

    @staticmethod
    def disable_by_group_event(group_event):
        GroupArtifactInfo.objects.filter(group_event_id=group_event.id).update(is_artifact_active=False)

    @staticmethod
    def get_active_artifacts(group_game_case_id):
        artifact_id_list = GroupArtifactInfo.objects.filter(is_artifact_active=True,
                                                            group_game_case_id=group_game_case_id)
        artifact_path_group = {}
        for group_artifact in artifact_id_list:
            if group_artifact.artifact.id not in artifact_path_group:
                if group_artifact.artifact_path:
                    path = group_artifact.artifact_path
                else:
                    path = group_artifact.artifact.path
                artifact_path_group[group_artifact.artifact.id] = path

        # recuperamos los artefactos para los ids recuperados
        artifacts = Artifact.objects.filter(id__in=artifact_path_group.keys())
        # Les ponemos el path que se haya definido para el usuario
        for artifact in artifacts:
            artifact.path = artifact_path_group[artifact.id]

        return artifacts

    @staticmethod
    def get_by_event_and_group(event_id, group_id):
        return GroupArtifactInfo.objects.filter(group_game_case__group_id=group_id,
                                                group_event__event_id=event_id,
                                                groupresponse__isnull=False).order_by('groupresponse__response_date')

    @staticmethod
    def get_by_event_and_user(event_id, user_id):
        return GroupArtifactInfo.objects.filter(group_game_case__group__users__exact=user_id,
                                                group_event__event_id=event_id,
                                                groupresponse__isnull=False).order_by('groupresponse__response_date')


class HiddenInfoBusiness:
    @staticmethod
    def get_hack_commands(case_id, group_game_case_id):
        group_artifact_infos = GroupArtifactInfo.objects.filter(group_game_case_id=group_game_case_id,
                                                                artifact__case_id=case_id).order_by('artifact_id')
        artifact_commands = {}
        artifact_cmd_list = list()
        for group_artifact_info in group_artifact_infos:

            if group_artifact_info.artifact_id not in artifact_commands:
                artifact_cmd_list = list()
                artifact_commands[group_artifact_info.artifact_id] = artifact_cmd_list

            hidden_info_params = {}
            tool_param_values = ToolParameterValue.objects.filter(hidden_info_id=group_artifact_info.hidden_info_id) \
                .order_by('order')

            last_tool_id = 0
            command_index = 0
            for tool_param_value in tool_param_values:
                # if tool_param_value.tool_id not in hidden_info_params:
                if tool_param_value.tool_id != last_tool_id:
                    command_index += 1
                    command = list()
                    command.append(tool_param_value.tool.command)
                    hidden_info_params[command_index] = command
                else:
                    command = hidden_info_params[command_index]

                last_tool_id = tool_param_value.tool_id

                param_flag = ''
                if tool_param_value.param.parameter:
                    param_flag = tool_param_value.param.parameter

                cmd = param_flag + tool_param_value.value
                # Comprobamos si esta marcado que en este parametro inyectemos la clave
                if tool_param_value.add_key_code:
                    cmd += str(group_artifact_info.info_key)
                command.append(cmd)

            # pasamos la lista de comandos con sus parametros a una sola cadena de texto por comando
            for hidden_info_cmd in hidden_info_params.values():
                artifact_cmd_list.append(' '.join(hidden_info_cmd))

        all_commands = list()
        return_value = ''
        for artifact_cmd in artifact_commands.values():
            if artifact_cmd:
                all_commands.append("\nRUN " + '\nRUN '.join(artifact_cmd))
                return_value = '\n'.join(all_commands)

        logger.debug(return_value)
        return return_value


class GroupResponseBusiness:
    @staticmethod
    def add_response(group_artifact_info_id, player_comment):
        group_artifact_info = GroupArtifactInfo.objects.get(id=group_artifact_info_id)

        GroupResponse.objects.create(group_game_case=group_artifact_info.group_game_case,
                                     group_artifact_info_id=group_artifact_info.id,
                                     player_comment=player_comment,
                                     score=group_artifact_info.hidden_info.score)

        GroupGameCaseBusiness.update_total_score(group_game_case_id=group_artifact_info.group_game_case_id)

        return group_artifact_info.hidden_info

    @staticmethod
    def has_response(group_game_case_id, group_artifact_info_id):
        return 0 < GroupResponse.objects.filter(group_game_case_id=group_game_case_id,
                                                group_artifact_info_id=group_artifact_info_id).count()


class ContactBusiness:
    @staticmethod
    def add_contact(group_game_case_id, character):
        contact = Contact.objects.filter(group_game_case_id=group_game_case_id, character_id=character.id)
        if contact:
            contact = contact[0]
            contact.is_online = True
            contact.last_login = None
            contact.save()
        else:
            contact_avatar = ''
            if character.avatar:
                contact_avatar = character.avatar.url
            return Contact.objects.create(group_game_case_id=group_game_case_id,
                                          character_id=character.id,
                                          name=character.full_name,
                                          avatar=contact_avatar)

    @staticmethod
    def disconect_contacts(group_game_case_id, finish_date):
        # Desconectamos todos aquellos contactos que no pertenezcan a un evento activo
        contacts = Contact.objects.filter(group_game_case_id=group_game_case_id, is_online=True,
                                          group_game_case__groupevent__is_active=False)
        if contacts:
            if not finish_date:
                finish_date = datetime.now()
            for contact in contacts:
                if not contact.group_game_case.groupevent_set.filter(is_active=True):
                    contact.is_online = False
                    contact.last_login = finish_date
                    contact.save()


class ConversationBusiness:
    @staticmethod
    def get_conversation_by_ggc_and_story_msg(group_game_case_id, message_id):
        conversations = Conversation.objects.filter(group_game_case_id=group_game_case_id,
                                                    chatmessage__story_message_id=message_id)
        if conversations:
            return conversations[0]
        else:
            return None

    @staticmethod
    def add_story_message_to_conversation(group_game_case_id, message_id):
        # Comprobamos que no exista una conversacion con ese mensaje, si existe devolvemos la conversacion
        conversation = ConversationBusiness.get_conversation_by_ggc_and_story_msg(group_game_case_id=group_game_case_id,
                                                                                  message_id=message_id)
        if conversation:
            return conversation

        # Si no existe recuperamos la conversación mediante el personaje de la historia
        story_message = Message.objects.get(id=message_id)
        contact = Contact.objects.filter(group_game_case_id=group_game_case_id, character__message=story_message)
        if contact:
            contact = contact[0]
            conversation = Conversation.objects.filter(group_game_case_id=group_game_case_id, contact_id=contact.id)
            # Si no recuperamos la conversación hay que crearla
            if not conversation:
                conversation = Conversation.objects.create(group_game_case_id=group_game_case_id,
                                                           contact=contact)
            else:
                conversation = conversation[0]

            ChatMessage.objects.create(conversation=conversation,
                                       story_message=story_message,
                                       text_message=story_message.plane_text)
            return conversation


class PlayerRatingBusiness:
    @staticmethod
    def toggle_player_rating(group_artifact_info_id, user_id, score):
        gartifact_info = GroupArtifactInfo.objects.filter(id=group_artifact_info_id)
        if gartifact_info.exists():
            player_rating = PlayerRating.objects.filter(
                group_response__group_artifact_info_id=group_artifact_info_id, player_id=user_id)
            # Si ya existia la valoración la eliminamos, y sino la damos de alta
            if player_rating.exists():
                player_rating.delete()
            else:
                PlayerRating.objects.create(group_response=gartifact_info[0].groupresponse, player_id=user_id,
                                            score=score)
                
class LearnTrackBusiness:
    @staticmethod
    def register_activity(user_id,code,description,related_to=0):
        usuario=User.objects.get(id=user_id)
        evt=LearnActivity(user=usuario,code=code,related=related_to,description=description)
        evt.save()
        
