import logging
import os
import re

logger = logging.getLogger(__name__)

CONFIG_PARAM_PATTERN = '({%\\s*\\w+\\s*%})'


def text_params_binding(text, params, pattern=CONFIG_PARAM_PATTERN):
    text_params_found = re.findall(pattern, text)
    if text_params_found:
        for param in text_params_found:
            value = ''
            if CONFIG_PARAM_PATTERN == pattern:
                key = param[2:-2].strip()
            else:
                key = param.strip()
            if key in params:
                value = params[key]
            text = text.replace(param, value)
    return text


def extract_zipfile(extraction_path, zip_file):
    # Creamos la carpeta donde descomprimir
    try:
        os.mkdir(extraction_path)
    except Exception:
        pass

    extract_files_path = list()
    # Extraemos todos los ficheros para que pueda ser procesado el dockerfile con los recursos que necesite
    for filename in zip_file.namelist():

        logger.debug("file: %s", filename)
        path = os.path.join(extraction_path, filename)
        # Si es un directorio, lo creamos
        if filename.endswith('/'):
            try:  # Intentamos generar los directorios que falten
                os.mkdir(path)
            except Exception:
                pass
        # Si es un fichero, lo escribimos
        else:
            outfile = open(path, 'wb')
            outfile.write(zip_file.read(filename))
            outfile.close()
            extract_files_path.append(path)
    return extract_files_path
