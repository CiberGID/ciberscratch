import os
import logging
import docker
import threading
from django.conf import settings
from paramiko import SSHClient, AutoAddPolicy
from scp import SCPClient

logger = logging.getLogger(__name__)

DOCKER_PARAM_PATTERN = "(\\${\\w+})"
GUACAMOLE_PROTOCOL = 'guacamole'
MARIADB_PROTOCOL = 'mariadb'


def get_docker_client():
    if settings.DOCKER_TLS_ENABLE:
        tls_config = docker.tls.TLSConfig(
            client_cert=(os.path.join(settings.MEDIA_ROOT, 'cert.pem'), os.path.join(settings.MEDIA_ROOT, 'key.pem'))
        )
        return docker.DockerClient(version='auto', base_url=settings.DOCKER_HOST_URL, tls=tls_config)
    else:
        return docker.DockerClient(version='auto', base_url=settings.DOCKER_HOST_URL, tls=False)


def start_container(protocol, image_name, container_name):
    client = get_docker_client()
    container = None
    if container_name:
        try:
            container = client.containers.get(container_id=container_name)
            if container.status == 'exited':
                container.start()
        except Exception as e:
            logger.error(e)

    # Si el contenedor no está arrancado lo levantamos
    if not container:
        auto_remove = protocol != MARIADB_PROTOCOL and protocol != GUACAMOLE_PROTOCOL
        ports_bindings = _define_container_protocol_ports(protocol)
        if container_name:
            # Si el contenedor ya existe, pero está parado, lo arrancamos
            container = client.containers.run(image=image_name,
                                              detach=True,
                                              auto_remove=auto_remove,
                                              tty=True,
                                              ports=ports_bindings,
                                              name=container_name)

        else:
            container = client.containers.run(image=image_name,
                                              detach=True,
                                              auto_remove=auto_remove,
                                              tty=True,
                                              ports=ports_bindings)

    if container:
        for it_container in client.containers.list():
            if it_container.name == container.name:
                return it_container


def build_image(image_name, path, buildargs):
    client = get_docker_client()

    try:
        # Comprobamos que no exista la imagen en el servidor
        client.images.get(image_name)
    except Exception:
        # Si no existe creamos la imagen
        try:
            client.images.build(path=path, nocache=True, buildargs=buildargs, tag=image_name, rm=True)
        except Exception as e:
            logger.error("Se ha generado una excepción en la construcción de la imagen docker. Revise que todos "
                         "los parametros están en el fichero de configuración.")
            raise e


def stop_container(container_name, commit=False, image_name=None):
    # Obtenemos el cliente docker
    client = get_docker_client()
    for container in client.containers.list():
        if container.name == container_name:
            # Hacemos commit del contenedor si así se ha indicado por parametro
            if commit and image_name:
                image = container.commit(repository=image_name)
                logger.info("Contenedor '%s' commiteado!\ttag: %s", container.name, image.tags)
            container.stop()
            logger.info("Contenedor '%s' parado", container.name)
            break


def _get_protocol_dict_key(protocol):
    if protocol == 'ssh':
        return '22/tcp'
    elif protocol == GUACAMOLE_PROTOCOL:
        return settings.GUACD_PORT + '/tcp'
    elif protocol == MARIADB_PROTOCOL:
        return '3306/tcp'


def _define_container_protocol_ports(protocol):
    dict_key = _get_protocol_dict_key(protocol)
    if protocol == 'ssh':
        return {dict_key: None}
    elif protocol == GUACAMOLE_PROTOCOL:
        return {dict_key: settings.GUACD_PORT}
    elif protocol == MARIADB_PROTOCOL:
        return {dict_key: settings.MARIADB_PORT}
    # Si hay otros protocolos añadir sus puertos para exponerlos en los contenedores docker


def write_dockerfile(dockerfile_file, content):
    dockerfile_file.seek(0)
    dockerfile_file.write(content)
    dockerfile_file.truncate()
    dockerfile_file.close()


def get_container_expose_port(container, protocol):
    return container.ports[_get_protocol_dict_key(protocol)][0]['HostPort']


def get_container_port(container_name, protocol):
    # Obtenemos el cliente docker
    client = get_docker_client()
    container = client.containers.get(container_id=container_name)
    if container:
        return get_container_expose_port(container=container, protocol=protocol)


def download_file_from_container(group_artifact_info, temp_dir):
    ssh_client = SSHClient()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy())
    ssh_client.load_system_host_keys()
    ggc = group_artifact_info.group_game_case
    # Como vamos a hacer una conexion por ssh en la recuperación del puerto expuesto del contenedor forzamos
    # el protocolo a ssh
    ssh_client.connect(hostname=settings.DOCKER_HOST_ADDRESS,
                port=get_container_port(container_name=ggc.docker_container_name, protocol='ssh'),
                username=ggc.username, password=ggc.password)

    # SCPCLient takes a paramiko transport as an argument
    with SCPClient(ssh_client.get_transport()) as scp:
        scp.get(remote_path=group_artifact_info.artifact_path, local_path=temp_dir)


class AsyncImagePulling(threading.Thread):
    def __init__(self, image_names, *args, **kwargs):
        self.image_names = image_names
        super(AsyncImagePulling, self).__init__(*args, **kwargs)

    def run(self):
        client = get_docker_client()
        for image_name in self.image_names:
            try:
                client.images.get(image_name)
            except docker.errors.ImageNotFound:
                logger.info("Descargando imagen %s del hub" % image_name)
                client.images.pull(image_name)
            logger.info("Imagen %s descargada" % image_name)
