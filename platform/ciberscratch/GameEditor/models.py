from django.db import models
import os
from ciberscratch import settings
from django.contrib.auth.models import User


# activar modelos:
# python manage.py makemigrations
# python manage.py migrate

def get_image_path(instance, filename):
    '''
    Función que se encarga de calcular el directorio dónde debemos almacenar los ficheros
    :param instance: objeto de la base de datos
    :param filename: nombre del fichero a almacenar
    :return: la ruta completa al directorio donde debemos almacenar los ficheros
    '''
    if isinstance(instance, Game):
        return os.path.join(settings.GAME_REPOSITORY, str(instance.code), filename)
    else:
        os.path.join(settings.GAME_REPOSITORY, 'tmp')


##########################################################

class Game(models.Model):
    STATUS = (
        ('D', 'DEVELOPMENT'),
        ('P', 'PUBLISH'),
        ('R', 'RESTRICTED'),
        ('PR', 'PRIVATE')
    )

    title = models.CharField(max_length=200)
    code = models.CharField(max_length=200)
    subject = models.CharField(max_length=200, blank=True, null=True)
    version = models.CharField(max_length=25, blank=True, null=True)
    creator = models.CharField(max_length=200)
    language = models.CharField(max_length=200)
    date = models.DateTimeField(blank=True, null=True)
    rights = models.CharField(max_length=200, blank=True, null=True)
    description = models.CharField(max_length=1000, blank=True, null=True)
    # game_image = models.ImageField(upload_to=get_image_path, blank=True, null=True)
    game_image = models.CharField(max_length=200, blank=True, null=True)
    # para definir el estado del juego en el editor
    status = models.CharField(max_length=15, choices=STATUS)
    # propietario: quién inicia el proyecto o lo carga en la plataforma
    owner = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return "{0} ({1}-{2}). Por: {3})".format(self.title, self.code, self.version, self.creator)


###########################################################
class Character(models.Model):
    # varios personajes pueden pertenecer a un juego
    game = models.ForeignKey(Game, on_delete=models.CASCADE)


############################################################
class Case(models.Model):
    # un juego se compone de varios casos
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
