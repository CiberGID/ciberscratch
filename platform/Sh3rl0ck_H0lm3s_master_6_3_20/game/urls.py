from django.urls import path, re_path

from . import views
from player.views import course_list
from guacamole.views import tunnel

urlpatterns = [
    path('', course_list, name='game'),
    path('course_list/', course_list, name='course_list'),
    path('game_list/', views.game_list, name='game_list'),
    path('case_list/', views.case_list, name='case_list'),
    path('game_view/', views.game_view, name='game_view'),
    path('game_view/tunnel', tunnel, name='tunnel'),
    path('game_view/download_clue/<int:artifact_id>/', views.download_clue, name='download_clue'),
    path('game_view/ajax/validate_key_code/', views.validate_key_code, name='validate_key_code'),
    path('game_view/ajax/add_response/', views.add_response, name='add_response'),
    path('game_view/ajax/unlock_events/', views.unlock_events, name='unlock_events'),
    path('game_view/ajax/get_current_events_messages/', views.get_current_events_messages,
         name='get_current_events_messages'),
    path('game_view/ajax/send_chat_message/', views.send_chat_message, name='send_chat_message'),
    path('game_view/ajax/validate_chat_message/', views.validate_chat_message, name='validate_chat_message'),
    path('game_view/ajax/get_unread_message/', views.get_unread_message, name='get_unread_message'),
    path('game_view/ajax/mark_as_read_chat_message/', views.mark_as_read_chat_message,
         name='mark_as_read_chat_message'),

    path('exit_game/', views.exit_game, name='exit_game'),

    path('ajax/generate_container/', views.generate_container, name='generate_container'),
    path('ajax/get_story_message/', views.get_story_message, name='get_story_message'),
    path('ajax/get_case_title/', views.get_case_title, name='get_case_title'),

    path('case_ranking/<int:case_id>/', views.case_ranking, name='case_ranking'),
    path('case_detail/<int:case_id>/<int:group_id>/', views.case_detail, name='case_detail'),
    path('event_detail/<int:event_id>/<int:group_id>/', views.event_detail, name='event_detail'),
    path('event_detail/<int:event_id>/<int:group_id>/ajax/response_player_like/', views.response_player_like,
         name='response_player_like'),
]
