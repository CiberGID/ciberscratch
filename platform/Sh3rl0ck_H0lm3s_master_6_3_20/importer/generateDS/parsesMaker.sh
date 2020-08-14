#!/usr/bin/env bash

PYTHON_COMMAND="python3"
PYTHON_VERSION=$($PYTHON_COMMAND --version)

XSD_HOME="../static/xsd"
OUTPUT_PATH="../parsers/"

echo Versión utilizada de $PYTHON_VERSION
echo
echo Iniciando generador de parseadores
echo ----------------------------------
for file in $XSD_HOME/*.xsd; do
    filename=$(basename -- "$file")
    filename="${filename%.*}"
    echo Generando modelo de \"$filename\"
    python3 generateDS.py --external-encoding=utf-8 -f -o "$OUTPUT_PATH$filename.py" $file
done

echo
echo Se han generado los modelos encontrados
