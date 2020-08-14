from django.contrib import admin
from .models import \
    Artifact, \
    ArtifactType, \
    Case, \
    Character, \
    Clue, \
    Course, \
    Department, \
    Event, \
    Game, \
    HiddenInfo, \
    HidingType, \
    Message, \
    Story, \
    StoryType, \
    Tool, \
    ToolParamValue, \
    ToolParameter, \
    Tools

admin.site.register(Artifact)
admin.site.register(ArtifactType)
admin.site.register(Case)
admin.site.register(Character)
admin.site.register(Clue)
admin.site.register(Course)
admin.site.register(Department)
admin.site.register(Event)
admin.site.register(Game)
admin.site.register(HiddenInfo)
admin.site.register(HidingType)
admin.site.register(Message)
admin.site.register(Story)
admin.site.register(StoryType)
admin.site.register(Tool)
admin.site.register(ToolParamValue)
admin.site.register(ToolParameter)
admin.site.register(Tools)

