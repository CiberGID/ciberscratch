------------------------------------------------------------------------------------
-- CONFIGURACION DE PERMISOS Y ROLES
-- Creamos el grupo Profesorado
INSERT INTO auth_group (name)
VALUES ('Profesorado');

-- Asignamos al rol Profesorado los permisos de juegos y usuarios
INSERT INTO auth_group_permissions (group_id, permission_id)
SELECT G.id, P.id
FROM auth_group G,
     auth_permission P
         JOIN django_content_type CT ON (CT.id = P.content_type_id)
WHERE G.name = 'Profesorado'
    AND CT.app_label IN ('game', 'player')
   OR (CT.app_label = 'auth' AND CT.model = 'user');

------------------------------------------------------------------------------------
-- CONFIGURACIÓN INICIAL DE JUEGO
-- Damos de alta el tipo de historia PDF
INSERT INTO "main"."game_storytype" ("name", "description")
VALUES ('pdf', 'PDF');
-- Damos de alta el tipo de historia chat
INSERT INTO "main"."game_storytype" ("name", "description")
VALUES ('chat', 'chat');
INSERT INTO "main"."game_storytype" ("name", "description")
VALUES ('email', 'email');
INSERT INTO "main"."game_storytype" ("name", "description")
VALUES ('html', 'html');
INSERT INTO "main"."game_storytype" ("name", "description")
VALUES ('audio', 'audio');
INSERT INTO "main"."game_storytype" ("name", "description")
VALUES ('movie', 'movie');

