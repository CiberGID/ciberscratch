import logging
import os
import tempfile
from datetime import datetime
from zipfile import ZipFile, BadZipfile
from django.core.files.base import ContentFile
from django import forms
from django.core.files.storage import default_storage
from django.contrib.auth.models import User
from common.validators import validate_import_file_extension
from django.contrib.admin.widgets import FilteredSelectMultiple
from common.widgets import CustomFileInput, CustomSelect
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from player.models import Course, Group

logger = logging.getLogger(__name__)


class UploadForm(forms.Form):
    file = forms.FileField(validators=[validate_import_file_extension], required=True, label=_("Fichero ZIP"),
                           widget=CustomFileInput(attrs={'class': 'custom-file-input'}))

    def clean_file(self):
        """
        Almacena en disco el fichero.
        Comprueba que el zip no está corrupto.
        Devuelve el path absoluto a dicho fichero.
        :return:
        """

        def ffile_path(uploaded_file):
            """
            Converts InMemoryUploadedFile to on-disk file so it will have path.
            :param uploaded_file:
            :return: path
            """
            try:
                return uploaded_file.temporary_file_path()
            except AttributeError:
                fileno, path = tempfile.mkstemp()
                temp_file = os.fdopen(fileno, 'w+b')
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file.close()
                return path

        path = ffile_path(self.cleaned_data['file'])

        try:  # Comprobación de que el fichero no está corrupto
            zf = ZipFile(path)
            bad_file = zf.testzip()
            if bad_file:
                raise forms.ValidationError(_('El fichero "%s" del ZIP está corrupto.' % bad_file))
            zf.close()
        except BadZipfile:
            raise forms.ValidationError(_('El fichero subido no es un ZIP.'))

        return path

    def process_file(self, request):
        # Ruta donde se encuentra el fichero
        zip_filename = self.cleaned_data['file']

        # Salvamos el fichero y lo procesamos
        date = timezone.now()
        # file_name = '{0}.{1}_{2}'.format(date.hour, date.minute, zip_filename)
        file_name = '{0}.{1}_import_upload'.format(date.hour, date.minute)
        logger.info("filename: %s", file_name)

        # Lugar donde se alojarán los ficheros descomprimidos
        dirname = os.path.join('uploads',
                               '{0}_{1}_{2}'.format(date.year, date.month, date.day),
                               'user_{0}'.format(request.user.id))

        logger.debug("path de subida del zip: %s", dirname)
        dirname = os.path.join(settings.MEDIA_ROOT, dirname)

        request.session['import_path'] = dirname

        upload_path = os.path.join(dirname, file_name)
        default_storage.save(upload_path + ".zip", ContentFile(open(zip_filename, 'rb').read()))
        zip = ZipFile(zip_filename)

        file_list = []

        # Creamos la carpeta donde descomprimir
        try:
            os.mkdir(upload_path)
        except Exception:
            pass

        request.session['import_path'] = upload_path

        # Recorremos todos los ficheros que contiene el zip
        for filename in zip.namelist():

            logger.debug("file: %s", filename)
            path = os.path.join(upload_path, filename)
            # Si es un directorio, lo creamos
            if filename.endswith('/'):
                try:  # Intentamos generar los directorios que falten
                    os.mkdir(path)
                except Exception:
                    pass
            # Si es un fichero, lo escribimos
            else:
                outfile = open(path, 'wb')
                outfile.write(zip.read(filename))
                outfile.close()
                file_list.append(path)

        zip.close()

        try:
            os.unlink(zip_filename)
        except Exception as e:
            logger.error(e)

        return file_list


class SelectXmlFiles(forms.Form):
    file = forms.ChoiceField(choices=(), required=True, label=_("Fichero XML a importar"),
                             # widget=CustomSelect(attrs={'class': 'select-field'})
                             )

    def __init__(self, *args, **kwargs):
        xml_files = kwargs.pop('xml_files', None)
        import_path = kwargs.pop('import_path', None)
        super(SelectXmlFiles, self).__init__(*args, **kwargs)
        self.fields['file'].choices = self.__get_xml_filename(xml_files=xml_files, import_path=import_path)

    @staticmethod
    def __get_xml_filename(xml_files, import_path=None):
        xml_filenames = list()
        if xml_files:
            for xml_file in xml_files:
                if import_path:
                    relative_file = xml_file[len(import_path) + 1:]
                else:
                    relative_file = xml_file
                xml_filenames.append((xml_file, relative_file))
        return xml_filenames


class XMLUploadForm(forms.Form):
    file = forms.FileField(validators=[validate_import_file_extension], required=True, label=_("Fichero XML"),
                           widget=CustomFileInput(attrs={'class': 'custom-file-input'}))

    def clean_file(self):
        """
        Almacena en disco el fichero.
        Devuelve el path absoluto a dicho fichero.
        :return:
        """

        def ffile_path(uploaded_file):
            """
            Converts InMemoryUploadedFile to on-disk file so it will have path.
            :param uploaded_file:
            :return: path
            """
            try:
                return uploaded_file.temporary_file_path()
            except AttributeError:
                fileno, path = tempfile.mkstemp()
                temp_file = os.fdopen(fileno, 'w+b')
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file.close()
                return path

        return ffile_path(self.cleaned_data['file'])

    def process_file(self, request):
        # Ruta donde se encuentra el fichero
        xml_filename = self.cleaned_data['file']

        # Salvamos el fichero y lo procesamos
        date = timezone.now()
        # file_name = '{0}.{1}_{2}'.format(date.hour, date.minute, zip_filename)
        file_name = '{0}.{1}_import_upload'.format(date.hour, date.minute)
        logger.info("filename: %s", file_name)

        # Lugar donde se alojarán los ficheros descomprimidos
        dirname = os.path.join('uploads',
                               '{0}_{1}_{2}'.format(date.year, date.month, date.day),
                               'user_{0}'.format(request.user.id))

        logger.debug("path de subida del xml: %s", dirname)
        dirname = os.path.join(settings.MEDIA_ROOT, dirname)

        request.session['import_path'] = dirname

        upload_path = os.path.join(dirname, file_name + ".xml")
        default_storage.save(upload_path, ContentFile(open(xml_filename, 'rb').read()))

        request.session['import_path'] = upload_path

        try:
            os.unlink(xml_filename)
        except Exception as e:
            logger.error(e)

        return upload_path


def _get_years():
    year_dropdown = []
    for y in range((datetime.now().year - 1), (datetime.now().year + 3)):
        year_dropdown.append((y, y))
    return year_dropdown


class SelectCourseForm(forms.Form):
    courses = forms.ModelChoiceField(queryset=Course.objects.all(), label=_("Asignatura"), required=True)
    year = forms.ChoiceField(choices=_get_years(), initial=datetime.now().year, label=_("Año"), required=True)


# class SelectGameForm(forms.Form):
#     course = forms.CharField(disabled=True, label=_("Asignatura"), required=True,
#                              widget=forms.TextInput(attrs={'class': 'placeholder-hide'}))
#
#     game = forms.ChoiceField(choices=(), required=True, label=_("Juego"),
#                              widget=CustomSelect(attrs={'class': 'select-field'}))
#
#     def __init__(self, *args, **kwargs):
#         if kwargs and 0 < len(kwargs):
#             course = kwargs.pop('course')
#             games = kwargs.pop('games')
#
#         super(SelectGameForm, self).__init__(*args, **kwargs)
#         if 1 == len(course):
#             self.fields['course'].initial = course[0].name
#         self.fields['game'].choices = self.__get_games(games=games)
#
#     @staticmethod
#     def __get_games(games):
#         game_list = list()
#         for game in games:
#             g = list()
#             g.append(game.id)
#             g.append(game.name)
#             game_list.append(g)
#
#         return game_list
