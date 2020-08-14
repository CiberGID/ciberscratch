from django.urls import path

from . import views


urlpatterns = [
    path('', views.upload_file, name='import'),
    path('datas', views.upload_file, name='import_datas'),
    path('select_xml', views.select_xml, name='select_xml'),
    path('users', views.users_import_view, name='import_users'),
]

