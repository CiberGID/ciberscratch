from django import forms


class Artifact(forms.Form):
    name = forms.CharField(max_length=1000, )
    description = forms.CharField(max_length=1000, blank=True, null=True)
    path = forms.CharField(max_length=1000, blank=True, null=True)
    artifact_type = forms.MultipleChoiceField(ArtifactType.objects.all())
    hidden_info = forms.MultipleChoiceField(HiddenInfo.objects.all())

class ArtifactType(forms.Form):
    name = forms.CharField(max_length=1000, )
    description = forms.CharField(max_length=1000, blank=True, null=True)

class Case(forms.Form):
    game_id = forms.IntegerField(blank=True, null=True)
    name = forms.CharField(max_length=1000, )
    description = forms.CharField(max_length=1000, blank=True, null=True)
    published_date = forms.DateTimeField(blank=True, null=True)
    is_published = forms.NullBooleanField()
    base_img_path = forms.CharField(max_length=1000, )
    case_image = forms.CharField(max_length=1000, blank=True, null=True)
    protocol = forms.CharField(max_length=1000, blank=True, null=True)
    terminal_username = forms.CharField(max_length=1000, blank=True, null=True)
    character = forms.MultipleChoiceField(Character.objects.all())
    story = forms.MultipleChoiceField(Story.objects.all())
    event = forms.MultipleChoiceField(Event.objects.all())
    artifact = forms.MultipleChoiceField(Artifact.objects.all())

class Character(forms.Form):
    character_key = forms.CharField(max_length=1000, )
    name = forms.CharField(max_length=1000, )
    full_name = forms.CharField(max_length=1000, )
    mail_address = forms.CharField(max_length=1000, blank=True, null=True)
    avatar_path = forms.CharField(max_length=1000, blank=True, null=True)

class Clue(forms.Form):
    order = forms.IntegerField()
    cost = forms.IntegerField(blank=True, null=True)
    clue_text = forms.CharField(max_length=1000, )

class Course(forms.Form):
    name = forms.CharField(max_length=1000, )
    acronym = forms.CharField(max_length=1000, blank=True, null=True)
    course_image = forms.CharField(max_length=1000, blank=True, null=True)

class Department(forms.Form):
    name = forms.CharField(max_length=1000, )
    url = forms.CharField(max_length=1000, blank=True, null=True)
    course = forms.MultipleChoiceField(Course.objects.all())

class Event(forms.Form):
    event_key = forms.CharField(max_length=1000, blank=True, null=True)
    case_id = forms.IntegerField(blank=True, null=True)
    name = forms.CharField(max_length=1000, )
    description = forms.CharField(max_length=1000, blank=True, null=True)
    previous_event_key = forms.CharField(max_length=1000, blank=True, null=True)
    previous_event_id = forms.IntegerField(blank=True, null=True)
    delay_start = forms.IntegerField(blank=True, null=True)
    onfinish_cancel_active_events = forms.NullBooleanField(blank=True, null=True)
    event_intro_story = forms.MultipleChoiceField(Story.objects.all())
    event_end_story = forms.MultipleChoiceField(Story.objects.all())

class Game(forms.Form):
    course_id = forms.IntegerField()
    name = forms.CharField(max_length=1000, )
    description = forms.CharField(max_length=1000, blank=True, null=True)
    published_date = forms.DateTimeField(blank=True, null=True)
    is_published = forms.NullBooleanField()
    game_image = forms.CharField(max_length=1000, blank=True, null=True)
    case = forms.MultipleChoiceField(Case.objects.all())

class HiddenInfo(forms.Form):
    name = forms.CharField(max_length=1000, )
    description = forms.CharField(max_length=1000, blank=True, null=True)
    hiding_type_id = forms.IntegerField()
    score = forms.IntegerField(blank=True, null=True)
    event_key = forms.CharField(max_length=1000, blank=True, null=True)
    is_event_key_info = forms.NullBooleanField()
    common_key_code = forms.CharField(max_length=1000, blank=True, null=True)
    prefix_key_code = forms.CharField(max_length=1000, blank=True, null=True)
    suffix_key_code = forms.CharField(max_length=1000, blank=True, null=True)
    random_key_code_word = forms.NullBooleanField(blank=True, null=True)
    random_word_maxlength = forms.IntegerField(blank=True, null=True)
    toolParamValue = forms.MultipleChoiceField(ToolParamValue.objects.all())
    clue = forms.MultipleChoiceField(Clue.objects.all())

class HidingType(forms.Form):
    name = forms.CharField(max_length=1000, )
    description = forms.CharField(max_length=1000, blank=True, null=True)

class Message(forms.Form):
    order = forms.IntegerField(blank=True, null=True)
    delay_to_show = forms.IntegerField(blank=True, null=True)
    character_key = forms.CharField(max_length=1000, blank=True, null=True)
    plane_text = forms.CharField(max_length=1000, blank=True, null=True)
    file_path = forms.CharField(max_length=1000, blank=True, null=True)

class Story(forms.Form):
    name = forms.CharField(max_length=1000, )
    description = forms.CharField(max_length=1000, blank=True, null=True)
    story_type_id = forms.IntegerField()
    message = forms.MultipleChoiceField(Message.objects.all())

class StoryType(forms.Form):
    idx = forms.IntegerField()
    name = forms.CharField(max_length=1000, )
    description = forms.CharField(max_length=1000, blank=True, null=True)

class Tool(forms.Form):
    name = forms.CharField(max_length=1000, )
    description = forms.CharField(max_length=1000, blank=True, null=True)
    command = forms.CharField(max_length=1000, )
    hiding_type = forms.MultipleChoiceField(HidingType.objects.all())
    parameter = forms.MultipleChoiceField(ToolParameter.objects.all())

class ToolParamValue(forms.Form):
    param_id = forms.IntegerField()
    tool_id = forms.IntegerField()
    value = forms.CharField(max_length=1000, blank=True, null=True)
    add_key_code = forms.NullBooleanField(blank=True, null=True)

class ToolParameter(forms.Form):
    name = forms.CharField(max_length=1000, )
    description = forms.CharField(max_length=1000, blank=True, null=True)
    parameter = forms.CharField(max_length=1000, )

class Tools(forms.Form):
    tool = forms.MultipleChoiceField(Tool.objects.all())
