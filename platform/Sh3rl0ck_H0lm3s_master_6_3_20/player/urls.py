from django.urls import path

from . import views

urlpatterns = [
    path('', views.user_group_management, name='player'),
    path('player_management', views.user_group_management, name='user_group_management'),
    path('ajax/course_selected/', views.course_selected, name='users_group_course_selected'),
    path('ajax/group_enable_valuechange/', views.group_enable_valuechange, name='group_enable_valuechange'),
    path('ajax/create_usergroup/', views.create_usergroup, name='create_usergroup'),
    path('ajax/change_usergroup/', views.change_usergroup, name='change_usergroup'),
]
