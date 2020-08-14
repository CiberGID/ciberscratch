import importlib
import logging
import os
import xml.etree.ElementTree as ET
from lxml import etree
from Sh3rl0ck_H0lm3s.settings import BASE_DIR
from .importBusiness import ImportBusiness
from .parsers.model import parse
from .parsers.users import parse
from django.utils.translation import gettext_lazy as _


logger = logging.getLogger(__name__)

GENERAL_MODEL_TYPE = 'model'
USER_MODEL_TYPE = 'users'

GAME_MODEL_XML_SCHEMA = 'importer/static/xsd/model.xsd'
USER_MODEL_XML_SCHEMA = 'importer/static/xsd/users.xsd'


def validate_xml(xml_file, xsd_path):
    try:
        xsd_file = os.path.join(BASE_DIR, xsd_path)

        with open(xsd_file, 'rb') as xml_schema_file:
            schema_root = etree.XML(xml_schema_file.read())

        schema = etree.XMLSchema(schema_root)
        xmlparser = etree.XMLParser(schema=schema)

        with open(xml_file, 'rb') as xml_file:
            xml_data = xml_file.read()
            try:
                etree.fromstring(xml_data, xmlparser)
                return True
            except etree.XMLSchemaError:
                return False

    except Exception as e:
        logger.error(e)
        return False


def import_data(xml_file, import_path=None):

    bean = parse_data(xml_file=xml_file, model_type=GENERAL_MODEL_TYPE)
    if bean:
        import_business = ImportBusiness()
        xml_root = _get_xml_root(xml_file=xml_file)
        getattr(import_business, "insert_%s" % xml_root)(bean, import_path)
        return True


def parse_data(xml_file, model_type):

    if model_type == USER_MODEL_TYPE:
        xsd_path = USER_MODEL_XML_SCHEMA
    elif model_type == GENERAL_MODEL_TYPE:
        xsd_path = GAME_MODEL_XML_SCHEMA
    else:
        raise ValueError(_("Tipo de modelo no valido. Tiene que ser 'model' o 'users'."))

    is_valid = validate_xml(xml_file=xml_file, xsd_path=xsd_path)
    logger.info("Validación de xml: %s", is_valid)
    bean = None

    if is_valid:
        xml_type = _get_xml_root(xml_file=xml_file)

        logger.info("Nombre del modulo: %s", xml_type)

        # Aunque se haga una importación dinamica hay que añadir los import en la cabecera del fichero
        parser_module = importlib.import_module('importer.parsers')
        parser = getattr(parser_module, model_type)
        bean = parser.parse(xml_file, silence=True)

    return bean


def _get_xml_root(xml_file):
    root = ET.parse(xml_file).getroot()
    logger.info("importing %s", root.tag)
    return root.tag[len('{https://game.sherlock_holmes.com}'):]
