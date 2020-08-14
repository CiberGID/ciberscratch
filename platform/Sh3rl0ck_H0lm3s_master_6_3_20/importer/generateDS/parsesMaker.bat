@echo off
title Sh3l0ck Parse Maker
Setlocal EnableDelayedExpansion

for /f "delims=" %%a in ('python --version') do @set PYTHON_VERSION=%%a

SET XSD_HOME=..\static\xsd
SET OUTPUT_PATH=..\parsers\

echo ############################################################################################
echo # AVISO: Si al generar la fuente para el parseado encuentra problemas de compilacion en la #
echo # misma por los cierres de comentario ejecute el script bash sobre un terminal Linux.      #
echo ############################################################################################
echo.
echo Version utilizada de %PYTHON_VERSION%
echo.
echo Iniciando generador de parseadores
echo ----------------------------------

for %%a in ("%XSD_HOME%\*") do (
    if "%%~xa" == ".xsd" (
        echo Generando modelo de "%%~na"
        python generateDS.py --external-encoding=utf-8 -f -o "%OUTPUT_PATH%%%~na.py" "%%a"
    )
)

echo.
echo Se han generado los modelos encontrados

