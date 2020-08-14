import logging
from django.apps import AppConfig
from django.conf import settings
from guacamole.utils import start_container, AsyncImagePulling
from guacamole.utils import GUACAMOLE_PROTOCOL, MARIADB_PROTOCOL

logger = logging.getLogger(__name__)


class GameConfig(AppConfig):
    name = 'game'

    def ready(self):
        # Comprobamos si esta levandado el contenedor mariadb y en caso contrario lo levantamos
        # try:
        #     container = start_container(protocol=MARIADB_PROTOCOL, image_name='sherlock_db:su',
        #                                 container_name='mariadbtest')
        #     logger.debug("Levantado contenedor %s", container.name)
        # except Exception as e:
        #     logger.error(e)

        # Comprobamos si esta levandado el contenedor guacd y en caso contrario lo levantamos
        try:
            container = start_container(protocol=GUACAMOLE_PROTOCOL, image_name='guacamole/guacd',
                                        container_name='guacd')
            logger.debug("Levantado contenedor %s", container.name)

            logger.debug("Descargando imagenes base si fuse necesario")
            AsyncImagePulling(settings.DOCKER_IMAGE_BASE).start()
        except Exception as e:
            logger.error(e)
