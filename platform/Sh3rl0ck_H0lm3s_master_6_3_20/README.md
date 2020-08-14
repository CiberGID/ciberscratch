# Juego Serio: Sh3rlock H0lme$

## Requisitos
Antes de instalar los requisitos python es necesario tener instalado en la maquina del desarrollador ciertas librearias dependiendo del entorno:
##### Windows
Es necesario tener[Microsoft Visual C++ 14.0](https://visualstudio.microsoft.com/es/downloads/). Los pasos a seguir son los siguientes:
1. Ir a la web https://visualstudio.microsoft.com/es/downloads/.
2. Descargar _Visual Studio 2019_, en concreto la versión ___Community___ y ejecutar el instalador.

3. En la pestaña Cargas de trabajo seleccionar el siguiente componente:
    * _Desarrollo para el escritorio con C++_ (dentro del apartado Windows)


##### Linux
Es necesario que el entorno tenga instalado python y las dependencias de desarrollo:
```bash
sudo apt update && sudo apt install python3 python3-pip python3-dev default-libmysqlclient-dev postgresql libpq-dev 
```
<!-- Se necesita tener instalado:
- [Django](https://docs.djangoproject.com/en/2.2/intro/install/#install-django)
- [Django Data Importer](https://django-data-importer.readthedocs.io/en/latest/index.html) para poder hacer un binding de los casos en xml a objetos python.
- [Django bootstrap4](https://django-bootstrap4.readthedocs.io/en/latest/#)
-->

##### Librerias Python
Todos los requisitos de librerias python están en el fichero requirements.txt y para instalar todo solo es necesario ejecutar:
```bash
pip install -r requirements.txt
```
En el caso de que se este en un entorno windows la libreria mysqlclient dará un error, esta libreria en concreto hay que instalarla manualmente:
1. Ir a la URL [Unofficial Windows Binaries for Python Extension Packages](https://www.lfd.uci.edu/~gohlke/pythonlibs/#mysqlclient).
2. Descargar la versión compatible para su windows y su versión de python.
3. Instalar manualmente el archivo descargado dirigiendose a la ruta en donde esté y ejecutando:
    ```bash
    pip install mysqlclient-1.4.4-cp37-cp37m-win32.whl
    ```

## Generación del modelo
Para la generación del modelo de juego se utilizan esquemas XML para su definición. De esta manera su posterior 
importacion mediante XML forzará que los datos tengan la estructura deseada.

Para generar el modelo se utiliza la utilidad [_generateDS_](http://www.davekuhlman.org/generateDS.html). En el proyecto
se encuentra la carpeta _generateDS_ con todo lo necesario. No obstante, es probable que sea necesario la instalación de 
la herramienta.

Requiere que python tenga instalada la dependencia six, requests y lxml. Para instalarla ejecutamos el siguiente comando:
```bash
pip install six requests lxml
```

Para generar el modelos mediante un XSD hay que ejecutar el siguiente comando en el terminal estando ubicados en el 
directorio _generateDS_.

```bash
python gends_run_gen_django.py -f -v --no-class-suffixes ../game/static/xsd/<esquema>.xsd
```

Esto generará multiples ficheros, los importantes para el proyecto son _models.py_, _forms.py_ y _admin.py_ cuyo 
contenido puede ser copiado en los propios ficheros del proyecto. Otro archivo generado importante es _esquemalib.py_,
el cual se deberá copiar en el directorio parsers. Este fichero es quien procesa un xml de entrada vinculado 
con el esquema y devuelve un objeto con los datos para su posterior importación en base de datos. 

# Preparar servidor Docker
Es necesario configurar Docker para las api remotas. Para ello es necesario añadir la siguiente linea al final del 
fichero /etc/default/docker
```
DOCKER_OPTS="-H tcp://0.0.0.0:2375 -H unix:///var/run/docker.sock"
```
El siguiente paso es reiniciar el servicio Docker:
```
sudo systemctl daemon-reload
sudo service docker restart
```


## Iniciar servidor apache guacamole con docker

Es necesario descargar en el servidor docker la imagen del servidor guacamole, para ello hay que ejecutar la siguiente
 sentencia en el equipo en el que corre docker:
```bash
docker pull guacamole/guacd
```
Aunque cuando la aplicacion se levanta comprueba que el contenedor docker con el servidor de apache guacamole esta 
activo y sino es así lo levanta, si se desea iniciar manualmente hay que ejecutar el siguiente comando:
```bash
docker run --rm --name guacd -d -p 4822:4822 guacamole/guacd
```

## Compilar literales localizados

Es necesario tener instalado la utilidad gettext tools.
##### linux
```bash
sudo apt install gettext
```
##### windows
* Es necesario descargar el instalador de [esta pagina](https://mlocati.github.io/articles/gettext-iconv-windows.html) con Flavor _static_ e instalarlo.
 
 Para compilar los literales que hay en la aplicacion, ya sea en los diferentes modulos python o en los templates, hay
que ejecutar el siguiente comando:
```bash
python manage.py  makemessages --ignore=generateDS* --ignore=importer/parsers/* --ignore=venv/* --locale sp
```
En este caso estamos volcando los mensajes al fichero .po correspondiente al español.

## Compilación de estilos SCSS

Si se desea compilar los ficheros .scss para que se genere el .css hay que ejecutar el siguiente comando:
```bash
python manage.py compilescss
```


## Para desplegar como contenedor Docker
```bash
docker-compose up
docker exec -it sh3rl0ck_h0lm3s_web_1 python manage.py migrate
docker exec -it sh3rl0ck_h0lm3s_web_1 python manage.py createsuperuser
```