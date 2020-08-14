import logging

from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from .models import Group, Case, GroupEvent, Event

logger = logging.getLogger(__name__)


def user_with_game_and_case_permission(func):
    """
    View decorator that checks a player have a game and case permission,
    in negative case the decorator return to home with a error message.
    """

    def wrapper(request, *args, **kwargs):
        logger.info("Entrando en el decorator user_with_game_and_case_permission")
        user_id = request.user.id
        if user_id:

            game_id = kwargs.get('game_id', None)
            if not game_id:
                if request.method == 'POST':
                    game_id = request.POST.get('game_id', None)
            if not game_id:
                game_id = request.session.get('game_id', None)

            case_id = kwargs.get('case_id', None)
            if not case_id:
                if request.method == 'POST':
                    case_id = request.POST.get('case_id', None)
            if not case_id:
                case_id = request.session.get('case_id', None)

            # Si no viene informado el id de juego pero si el del caso lo recuperamos de bbdd
            if case_id and not game_id:
                case = Case.objects.get(id=case_id)
                game_id = case.game_id

            if game_id and case_id:
                # Verificamos que para el grupo indicado se tiene permiso sobre el juego y el caso
                has_permission = 0 < Group.objects.filter(usergroup__player_id=user_id, course__game__exact=game_id,
                                                          course__game__case__exact=case_id).count()
                if has_permission:
                    return func(request, *args, **kwargs)
                else:
                    logger.error("Usuario con id %s intentando acceder sin privilegios a %s", user_id, request.path)

        messages.error(request, _("Carece de permiso para acceder a la página solicitada"))
        return redirect('home')

    return wrapper


def user_with_event_permission(func):
    """
        View decorator that checks a player have a event permission,
        in negative case the decorator return to home with a error message.
        """

    def wrapper(request, *args, **kwargs):
        logger.info("Entrando en el decorator user_with_event_permission")
        user_id = request.user.id
        has_permission = False
        if user_id:
            event_id = kwargs.get('event_id', None)
            if not event_id:
                if request.method == 'POST':
                    event_id = request.POST.get('event_id', None)
            if event_id:
                event = Event.objects.get(id=event_id)
                if request.user.is_staff:
                    case = event.case
                    has_permission = 0 < Group.objects.filter(usergroup__player_id=user_id,
                                                              course__game__exact=case.game_id,
                                                              course__game__case__exact=case.id).count()
                else:
                    # Verificamos que para el grupo indicado se tiene permiso sobre el evento
                    has_permission = GroupEvent.objects.filter(group_game_case__group__users__exact=user_id,
                                                               event_id=event_id,
                                                               finish_date__isnull=False, is_active=False).exists()
        if has_permission:
            return func(request, *args, **kwargs)
        else:
            logger.error("Usuario con id %s intentando acceder sin privilegios a %s", user_id, request.path)
        messages.error(request, _("Carece de permiso para acceder a la página solicitada"))
        return redirect('home')

    return wrapper
