"""Sh3rl0ck_H0lm3s URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from game.views import home, stop_docker_container_and_logout, add_messages_to_view, started_cases, finished_cases


urlpatterns = [
    path('', home, name='home'),
    path('started_cases', started_cases, name='started_cases'),
    path('finished_cases', finished_cases, name='finished_cases'),
    path('admin/', admin.site.urls),
    path('import/', include('importer.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('game/', include('game.urls')),
    path('logout/', stop_docker_container_and_logout, name='logout'),
    path('ajax/add_messages_to_view/', add_messages_to_view, name='add_messages_to_view'),
    path('player/', include('player.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

