from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class Validator:
    @staticmethod
    def validate_year(value):
        if value < 1990 or value > 2100:
            raise ValidationError(
                _('%s no es un valor de año válido' % value),
            )
