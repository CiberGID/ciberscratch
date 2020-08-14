from django import forms

from common.validators import validate_import_file_extension
from common.widgets import CustomSelect, CustomFileInput
from django.utils.translation import gettext_lazy as _


class StoryType(forms.Form):
    storyTypeId = forms.CharField(max_length=1000, )
    name = forms.CharField(max_length=1000, )
    description = forms.CharField(max_length=1000, )


class Tool(forms.Form):
    name = forms.CharField(max_length=1000, )
    description = forms.CharField(max_length=1000, )
    command = forms.CharField(max_length=1000, )
    toolId = forms.CharField(max_length=1000, )
    # parameters = forms.MultipleChoiceField(ToolParameter.objects.all())


class ToolParameter(forms.Form):
    name = forms.CharField(max_length=1000, )
    description = forms.CharField(max_length=1000, )
    parameter = forms.CharField(max_length=1000, )
    toolId = forms.CharField(max_length=1000, )


class ImportForm(forms.Form):
    roots = (
        ('T', 'Tool'),
        ('ST', 'StoryType'),
        ('S', 'Story'),
        ('A', 'Artifact'),
        ('AT', 'ArtifactType'),
        ('HT', 'HidingType'),
        ('HI', 'HiddenInfo'),
        ('C', 'Case'),
        ('G', 'Game'),
        ('E', 'Event'),
    )
    roots = sorted(roots, key=lambda x: x[1])

    root = forms.ChoiceField(choices=roots, required=True, label=_("Root del XML"),
                             widget=CustomSelect(attrs={'class': 'select-field'}))
    file = forms.FileField(validators=[validate_import_file_extension], required=True, label=_("Fichero XML"),
                           widget=CustomFileInput(attrs={'class': 'custom-file-input'})
                           )


class SelectGameForm(forms.Form):
    course = forms.CharField(disabled=True, label=_("Asignatura"), required=True,
                             widget=forms.TextInput(attrs={'class': 'placeholder-hide'}))

    game = forms.ChoiceField(choices=(), required=True, label=_("Juego"),
                             widget=CustomSelect(attrs={'class': 'select-field'}))

    def __init__(self, *args, **kwargs):
        if kwargs and 0 < len(kwargs):
            course = kwargs.pop('course')
            games = kwargs.pop('games')

        super(SelectGameForm, self).__init__(*args, **kwargs)
        if 1 == len(course):
            self.fields['course'].initial = course[0].name
        self.fields['game'].choices = self.__get_games(games=games)

    @staticmethod
    def __get_games(games):
        game_list = list()
        for game in games:
            g = list()
            g.append(game.id)
            g.append(game.name)
            game_list.append(g)

        return game_list


class KeyCodeForm(forms.Form):
    key_code = forms.UUIDField(required=False, label='',
                               widget=forms.TextInput(attrs={'placeholder': _('Introduzca la clave encontrada')})
                               )


class EventResponseForm(forms.Form):
    group_artifact_info = forms.IntegerField(widget=forms.HiddenInput)
    comment_key_code = forms.UUIDField(required=False, label=_('Clave encontrada'), disabled=True)
    comment = forms.CharField(max_length=4000, required=False, label=_('Comentarios de su solución'),
                              widget=forms.Textarea(attrs={'rows': 8,
                                                           'placeholder': _('En este campo puede detallar los pasos '
                                                                            'dados hasta llegar a la solución. '
                                                                            'Estos comentarios podrán ser visibles '
                                                                            'por otros compañeros que también '
                                                                            'lo hayan resuelto.')}))
