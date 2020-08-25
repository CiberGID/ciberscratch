from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class Validator:
    @staticmethod
    def validate_positive_number(value):
        if value < 0:
            raise ValidationError(
                _('%s no es un posible valor' % value),
            )
    @staticmethod
    def is_student(value):
        if value.is_staff or value.is_superuser:
            return False
        else:
            return True
    @staticmethod
    def is_lecturer(value):
        if value.is_staff:
            return True
        else:
            return False

    @staticmethod
    def validate_import_file_extension(value):
        import os
        from django.core.exceptions import ValidationError
        ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
        valid_extensions = ['.xml', '.zip']
        if not ext.lower() in valid_extensions:
            raise ValidationError(_('Extensión del fichero no soportada.'))

