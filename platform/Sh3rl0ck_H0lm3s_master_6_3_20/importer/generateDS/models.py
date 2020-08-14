from django.db import models


class Artifact(models.Model):
    name = models.CharField(max_length=1000, )
    description = models.CharField(max_length=1000, blank=True, null=True)
    path = models.CharField(max_length=1000, blank=True, null=True)
    artifact_type = models.ForeignKey(
        "ArtifactType",
        on_delete=models.CASCADE,
        related_name="Artifact_artifact_type_ArtifactType",
    )
    hidden_info = models.ForeignKey(
        "HiddenInfo",
        on_delete=models.CASCADE,
        related_name="Artifact_hidden_info_HiddenInfo",
        blank=True, null=True,
    )

    def __unicode__(self):
        return "id: %s" % (self.id, )


class ArtifactType(models.Model):
    name = models.CharField(max_length=1000, )
    description = models.CharField(max_length=1000, blank=True, null=True)

    def __unicode__(self):
        return "id: %s" % (self.id, )


class Case(models.Model):
    game_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=1000, )
    description = models.CharField(max_length=1000, blank=True, null=True)
    published_date = models.DateTimeField(blank=True, null=True)
    is_published = models.NullBooleanField()
    base_img_path = models.CharField(max_length=1000, )
    case_image = models.CharField(max_length=1000, blank=True, null=True)
    protocol = models.CharField(max_length=1000, blank=True, null=True)
    terminal_username = models.CharField(max_length=1000, blank=True, null=True)
    character = models.ForeignKey(
        "Character",
        on_delete=models.CASCADE,
        related_name="Case_character_Character",
        blank=True, null=True,
    )
    story = models.ForeignKey(
        "Story",
        on_delete=models.CASCADE,
        related_name="Case_story_Story",
    )
    event = models.ForeignKey(
        "Event",
        on_delete=models.CASCADE,
        related_name="Case_event_Event",
    )
    artifact = models.ForeignKey(
        "Artifact",
        on_delete=models.CASCADE,
        related_name="Case_artifact_Artifact",
    )

    def __unicode__(self):
        return "id: %s" % (self.id, )


class Character(models.Model):
    character_key = models.CharField(max_length=1000, )
    name = models.CharField(max_length=1000, )
    full_name = models.CharField(max_length=1000, )
    mail_address = models.CharField(max_length=1000, blank=True, null=True)
    avatar_path = models.CharField(max_length=1000, blank=True, null=True)

    def __unicode__(self):
        return "id: %s" % (self.id, )


class Clue(models.Model):
    order = models.IntegerField()
    cost = models.IntegerField(blank=True, null=True)
    clue_text = models.CharField(max_length=1000, )

    def __unicode__(self):
        return "id: %s" % (self.id, )


class Course(models.Model):
    name = models.CharField(max_length=1000, )
    acronym = models.CharField(max_length=1000, blank=True, null=True)
    course_image = models.CharField(max_length=1000, blank=True, null=True)

    def __unicode__(self):
        return "id: %s" % (self.id, )


class Department(models.Model):
    name = models.CharField(max_length=1000, )
    url = models.CharField(max_length=1000, blank=True, null=True)
    course = models.ForeignKey(
        "Course",
        on_delete=models.CASCADE,
        related_name="Department_course_Course",
    )

    def __unicode__(self):
        return "id: %s" % (self.id, )


class Event(models.Model):
    event_key = models.CharField(max_length=1000, blank=True, null=True)
    case_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=1000, )
    description = models.CharField(max_length=1000, blank=True, null=True)
    previous_event_key = models.CharField(max_length=1000, blank=True, null=True)
    previous_event_id = models.IntegerField(blank=True, null=True)
    delay_start = models.IntegerField(blank=True, null=True)
    onfinish_cancel_active_events = models.NullBooleanField(blank=True, null=True)
    event_intro_story = models.ForeignKey(
        "Story",
        on_delete=models.CASCADE,
        related_name="Event_event_intro_story_Story",
        blank=True, null=True,
    )
    event_end_story = models.ForeignKey(
        "Story",
        on_delete=models.CASCADE,
        related_name="Event_event_end_story_Story",
        blank=True, null=True,
    )

    def __unicode__(self):
        return "id: %s" % (self.id, )


class Game(models.Model):
    course_id = models.IntegerField()
    name = models.CharField(max_length=1000, )
    description = models.CharField(max_length=1000, blank=True, null=True)
    published_date = models.DateTimeField(blank=True, null=True)
    is_published = models.NullBooleanField()
    game_image = models.CharField(max_length=1000, blank=True, null=True)
    case = models.ForeignKey(
        "Case",
        on_delete=models.CASCADE,
        related_name="Game_case_Case",
    )

    def __unicode__(self):
        return "id: %s" % (self.id, )


class HiddenInfo(models.Model):
    name = models.CharField(max_length=1000, )
    description = models.CharField(max_length=1000, blank=True, null=True)
    hiding_type_id = models.IntegerField()
    score = models.IntegerField(blank=True, null=True)
    event_key = models.CharField(max_length=1000, blank=True, null=True)
    is_event_key_info = models.NullBooleanField()
    common_key_code = models.CharField(max_length=1000, blank=True, null=True)
    prefix_key_code = models.CharField(max_length=1000, blank=True, null=True)
    suffix_key_code = models.CharField(max_length=1000, blank=True, null=True)
    random_key_code_word = models.NullBooleanField(blank=True, null=True)
    random_word_maxlength = models.IntegerField(blank=True, null=True)
    toolParamValue = models.ForeignKey(
        "ToolParamValue",
        on_delete=models.CASCADE,
        related_name="HiddenInfo_toolParamValue_ToolParamValue",
        blank=True, null=True,
    )
    clue = models.ForeignKey(
        "Clue",
        on_delete=models.CASCADE,
        related_name="HiddenInfo_clue_Clue",
        blank=True, null=True,
    )

    def __unicode__(self):
        return "id: %s" % (self.id, )


class HidingType(models.Model):
    name = models.CharField(max_length=1000, )
    description = models.CharField(max_length=1000, blank=True, null=True)

    def __unicode__(self):
        return "id: %s" % (self.id, )


class Message(models.Model):
    order = models.IntegerField(blank=True, null=True)
    delay_to_show = models.IntegerField(blank=True, null=True)
    character_key = models.CharField(max_length=1000, blank=True, null=True)
    plane_text = models.CharField(max_length=1000, blank=True, null=True)
    file_path = models.CharField(max_length=1000, blank=True, null=True)

    def __unicode__(self):
        return "id: %s" % (self.id, )


class Story(models.Model):
    name = models.CharField(max_length=1000, )
    description = models.CharField(max_length=1000, blank=True, null=True)
    story_type_id = models.IntegerField()
    message = models.ForeignKey(
        "Message",
        on_delete=models.CASCADE,
        related_name="Story_message_Message",
    )

    def __unicode__(self):
        return "id: %s" % (self.id, )


class StoryType(models.Model):
    idx = models.IntegerField()
    name = models.CharField(max_length=1000, )
    description = models.CharField(max_length=1000, blank=True, null=True)

    def __unicode__(self):
        return "id: %s" % (self.id, )


class Tool(models.Model):
    name = models.CharField(max_length=1000, )
    description = models.CharField(max_length=1000, blank=True, null=True)
    command = models.CharField(max_length=1000, )
    hiding_type = models.ForeignKey(
        "HidingType",
        on_delete=models.CASCADE,
        related_name="Tool_hiding_type_HidingType",
        blank=True, null=True,
    )
    parameter = models.ForeignKey(
        "ToolParameter",
        on_delete=models.CASCADE,
        related_name="Tool_parameter_ToolParameter",
        blank=True, null=True,
    )

    def __unicode__(self):
        return "id: %s" % (self.id, )


class ToolParamValue(models.Model):
    param_id = models.IntegerField()
    tool_id = models.IntegerField()
    value = models.CharField(max_length=1000, blank=True, null=True)
    add_key_code = models.NullBooleanField(blank=True, null=True)

    def __unicode__(self):
        return "id: %s" % (self.id, )


class ToolParameter(models.Model):
    name = models.CharField(max_length=1000, )
    description = models.CharField(max_length=1000, blank=True, null=True)
    parameter = models.CharField(max_length=1000, )

    def __unicode__(self):
        return "id: %s" % (self.id, )


class Tools(models.Model):
    tool = models.ForeignKey(
        "Tool",
        on_delete=models.CASCADE,
        related_name="Tools_tool_Tool",
    )

    def __unicode__(self):
        return "id: %s" % (self.id, )

