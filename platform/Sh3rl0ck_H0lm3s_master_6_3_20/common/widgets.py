from django.forms import widgets


class CustomSelect(widgets.Select):
    template_name = 'widgets/custom_select.html'


class CustomFileInput(widgets.ClearableFileInput):
    template_name = 'widgets/custom_file_input.html'

