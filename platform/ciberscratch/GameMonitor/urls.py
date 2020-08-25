from django.urls import path

from . import views

app_name = 'GameMonitor'
urlpatterns = [
    path('update_profile/', views.update_profile, name="update_profile"),
    path('register_user', views.register_user_with_code, name='register_user'),
    path('edit_classroom/<int:class_id>/', views.manage_classroom, name='edit_classroom'),
    path('delete_classroom/<int:class_id>/', views.delete_classroom, name='delete_classroom'),
]
