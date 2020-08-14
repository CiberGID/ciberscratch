FROM autrilla14/base_ssh

ARG group=alumnos
ARG username
ARG welcome_message=''

#Creacion de usuarios especifica para Alpine
RUN addgroup -S ${group} \
&& adduser -S ${username} -s /bin/ash -G alumnos

#Cambiamos la contraseña del usuario
RUN echo "${username}:${username}" | chpasswd

#Establecemos el mensaje de bienvenida
RUN echo -e ${welcome_message} > /etc/motd

#Copiamos los recursos que se deseen
#ADD resources.tar.gz /
#COPY resources/* /home/${username}/

{%copyResources%}

#Establecemos al usuario como propietario del contenido de su home
RUN chown -R ${username}:${group} /home/${username}/
