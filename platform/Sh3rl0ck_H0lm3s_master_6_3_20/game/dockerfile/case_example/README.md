#### Los recursos a copiar
Deben estar comprimidos en la raiz en formato _.tar.gz_

**Comprimir**: `tar -czvf resources.tar.gz resources/`



#### Comando para contruir contenedor
`docker build 
-t sherlock/case1 
--build-arg username=alumnoX 
--build-arg welcome_message="Bienvenido al juego X\nNombre del caso\n\n\nBuena caza!" 
--no-cache .`


#### Comando para arrancar el contenedor
`docker run -it --rm 
-p _8787_:22 
--name case1 
sherlock/case1`