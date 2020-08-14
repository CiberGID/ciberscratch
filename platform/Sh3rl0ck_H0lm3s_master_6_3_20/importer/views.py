import logging
import re
import xml.etree.ElementTree as ET
from zipfile import ZipFile
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import IntegrityError, transaction
from .forms import UploadForm, SelectXmlFiles, XMLUploadForm, SelectCourseForm
from .importers import import_data, validate_xml
from shutil import rmtree
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from player.models import Course
from importer.importers import validate_xml, USER_MODEL_XML_SCHEMA, GAME_MODEL_XML_SCHEMA

logger = logging.getLogger(__name__)


@user_passes_test(lambda u: u.is_staff)
def upload_file(request):
    if request.method == 'POST':

        form = UploadForm(request.POST, request.FILES)

        # Si el formulario el válido, proceso el fichero
        if form.is_valid():
            zipdata = request.FILES['file']
            file_list = form.process_file(request=request)
            xml_files = list()

            for file_path in file_list:
                logger.debug("Data: %s", file_path)
                if file_path.lower().endswith('.xml'):
                    xml_files.append(file_path)

            logger.debug("ficheros filtrados: %s", xml_files)

            if 0 == len(xml_files):
                logger.info("No se han encontrado ficheros xml en la raíz")
                messages.warning(request, _("No se han encontrado ficheros xml en la raíz"))
            else:
                # Si hay varios xml en la raiz permitimos seleccionar el deseado
                request.session['xml_file_list'] = xml_files

                return redirect('select_xml')
    else:
        form = UploadForm()
    return render(request, 'import_data.html', {'form': form,
                                                'title': _('Importar Datos de Juego'),
                                                'button_name': _('Subir')})


@user_passes_test(lambda u: u.is_staff)
@transaction.atomic
def select_xml(request):
    def _xml_selected(request, xml_file):
        try:
            # Si se produce alguna excepcion durante la importación se hace un rollback de todos
            with transaction.atomic():
                is_valid = validate_xml(xml_file=xml_file,  xsd_path=GAME_MODEL_XML_SCHEMA)
                import_path = request.session['import_path']
                if not is_valid:
                    logger.info("El XML no es válido")
                    messages.error(request, _("El XML no es válido"))
                elif is_valid and import_data(xml_file=xml_file, import_path=import_path):
                    logger.info("La Importación se ha realizado satisfactoriamente")
                    messages.success(request, _("La Importación se ha realizado satisfactoriamente"))
                    # Eliminamos el contenido descomprimido
                    rmtree(import_path)
        except IntegrityError as e:
            messages.error(request, e)

        # Limpiamos variables de session
        request.session['xml_file_list'] = None
        request.session['import_path'] = None

        return redirect('/import/')

    xml_files = request.session['xml_file_list']
    if request.method == 'POST':
        form = SelectXmlFiles(request.POST, xml_files=xml_files)
        if form.is_valid():
            file = form.cleaned_data['file']
            xml_file = dict(form.fields['file'].choices)[file]
            logger.debug("file selected: %s", xml_file)

            return _xml_selected(request, xml_file)
    else:
        if 1 == len(xml_files):
            # Si solo hay un xml los seleccionamos
            return _xml_selected(request, xml_files[0])
        else:
            import_path = request.session['import_path']
            form = SelectXmlFiles(xml_files=xml_files, import_path=import_path)

    return render(request, 'select_xml_file.html', {'form': form,
                                                    'title': _("Seleccionar XML a importar")})


@user_passes_test(lambda u: u.is_staff)
def users_import_view(request):
    if request.method == 'POST':

        form = XMLUploadForm(request.POST, request.FILES)

        # Si el formulario el válido, proceso el fichero
        if form.is_valid():
            file_path = form.process_file(request=request)
            logger.debug("Data: %s", file_path)

            if not file_path and not file_path.lower().endswith('.xml'):
                logger.info("No se ha espeficiado un XML válido")
                messages.warning(request, _("No se ha espeficiado un XML válido"))
            else:
                # Validamos que el xml cumple el esquema
                if validate_xml(xml_file=file_path, xsd_path=USER_MODEL_XML_SCHEMA):
                    request.session['user_xml_path'] = file_path
                    return redirect('user_group_management')
                else:
                    messages.error(request, _("XML no válido"))
        else:
            messages.error(request, form.errors['file'])

    form_upload = XMLUploadForm()
    return render(request, 'import_users.html', {'form_upload': form_upload,
                                                 'title': _('Importar Usuarios')})


def _get_zip_files(tmp_file):
    zip = ZipFile(tmp_file)
    datas = zip.infolist()
    xml_files = list()
    # Buscamos ficheros xml
    pattern = re.compile("^([\w\s])*.(xml)")
    for data in datas:
        logger.debug("Data: %s", data)
        if not data.is_dir() and pattern.match(data.filename):
            xml_files.append(data)
    return xml_files
