from django.contrib import admin
from django.urls import reverse
from django.utils import html
from .models import *


@admin.register(StoryType)
class StoryTypeAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'name', 'description')
    search_fields = ('id', 'name',)


@admin.register(Tool)
class ToolAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'name', 'command', 'description')
    search_fields = ('id', 'name', 'command')


@admin.register(ToolParameter)
class ToolParameterAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'link_to_tool', 'name', 'parameter')
    search_fields = ('id', 'name',)

    def link_to_tool(self, obj):
        link = reverse("admin:game_tool_change", args=[obj.tool.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.tool.name)

    link_to_tool.short_description = 'Tool'


@admin.register(Story)
class StoryAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'name', 'description', 'story_type_name')
    search_fields = ('id', 'name',)

    def story_type_name(self, obj):
        return obj.story_type.name

    story_type_name.short_description = 'Story Type'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'story_id', 'story', 'delay_to_show', 'order')
    search_fields = ('id', 'story__id', 'story__name')

    def story_id(self, obj):
        return obj.story.id

    story_id.short_description = 'Story Id'


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'name', 'link_to_course', 'creation_date', 'published_date', 'is_published')
    search_fields = ('id', 'name',)
    actions = ['make_published']

    def make_published(self, request, queryset):
        queryset.update(is_published=True, published_date=timezone.now())

    make_published.short_description = "Mark selected game as published"

    def link_to_course(self, obj):
        link = reverse("admin:player_course_change", args=[obj.course.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.course.name)

    link_to_course.short_description = 'Course'


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'name', 'link_to_game', 'creation_date', 'published_date', 'is_published', 'protocol')
    search_fields = ('id', 'name',)
    actions = ['make_published']

    def make_published(self, request, queryset):
        queryset.update(is_published=True, published_date=timezone.now())

    make_published.short_description = "Mark selected game as published"

    def link_to_game(self, obj):
        link = reverse("admin:game_game_change", args=[obj.game.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.game.name)

    link_to_game.short_description = 'Game'


@admin.register(HidingType)
class HidingTypeAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'name', 'link_to_tool')
    search_fields = ('id', 'name',)

    def link_to_tool(self, obj):
        link = reverse("admin:game_tool_change", args=[obj.tool.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.tool.name)

    link_to_tool.short_description = 'Tool'


@admin.register(HiddenInfo)
class HiddenInfoAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'name', 'score', 'link_to_artifact', 'link_to_event', 'is_event_key', 'common_key_code',
                    'prefix_key_code', 'suffix_key_code', 'random_key_code_word')
    search_fields = ('id', 'name', 'common_key_code')

    def link_to_artifact(self, obj):
        link = reverse("admin:game_artifact_change", args=[obj.artifact.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.artifact.name)

    link_to_artifact.short_description = 'Artifact'

    def link_to_event(self, obj):
        link = reverse("admin:game_event_change", args=[obj.event.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.event.name)

    link_to_event.short_description = 'Event'


@admin.register(ArtifactType)
class ArtifactTypeAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'name')
    search_fields = ('id', 'name',)


@admin.register(Artifact)
class ArtifactAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'name', 'path', 'link_to_artifact_type')
    search_fields = ('id', 'name',)

    def link_to_artifact_type(self, obj):
        link = reverse("admin:game_artifacttype_change", args=[obj.artifact_type.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.artifact_type.name)

    link_to_artifact_type.short_description = 'Artifact Type'


@admin.register(ToolParameterValue)
class ToolParameterValueAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'link_to_param', 'link_to_tool', 'link_to_hidden_info', 'value', 'add_key_code')
    search_fields = ('id', 'name',)

    def link_to_param(self, obj):
        link = reverse("admin:game_toolparameter_change", args=[obj.param.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.param.name)

    link_to_param.short_description = 'Parameter'

    def link_to_tool(self, obj):
        link = reverse("admin:game_tool_change", args=[obj.tool.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.tool.name)

    link_to_tool.short_description = 'Tool'

    def link_to_hidden_info(self, obj):
        link = reverse("admin:game_hiddeninfo_change", args=[obj.hidden_info.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.hidden_info.name)

    link_to_hidden_info.short_description = 'Hidden Info'


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'name', 'link_to_intro_story', 'link_to_end_story', 'link_to_previous_event', 'delay_start',
                    'onfinish_cancel_active_events')
    search_fields = ('id', 'name',)

    def link_to_intro_story(self, obj):
        link = reverse("admin:game_story_change", args=[obj.event_intro_story.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.event_intro_story.name)

    link_to_intro_story.short_description = 'Intro Story'

    def link_to_end_story(self, obj):
        link = reverse("admin:game_story_change", args=[obj.event_end_story.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.event_end_story.name)

    link_to_end_story.short_description = 'End Story'

    def link_to_previous_event(self, obj):
        if not obj.previous_event:
            return '-'
        else:
            link = reverse("admin:game_event_change", args=[obj.previous_event.id])  # model name has to be lowercase
            return html.format_html('<a href="{}">{}</a>', link, obj.previous_event.name)

    link_to_previous_event.short_description = 'Previous Event'

    def link_to_hidden_info_key(self, obj):
        link = reverse("admin:game_hiddeninfo_change", args=[obj.hidden_info_eventKey.id])
        return html.format_html('<a href="{}">{}</a>', link, obj.hidden_info_eventKey.name)

    link_to_hidden_info_key.short_description = 'Hidden Info Key'


@admin.register(GroupGameCase)
class GroupGameCaseAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'link_to_group', 'link_to_game', 'link_to_case',
                    'start_date', 'finish_date', 'total_score', 'docker_image_name', 'docker_container_name')
    search_fields = ('id', 'game__name', 'case__name', 'group__name')

    def link_to_game(self, obj):
        link = reverse("admin:game_game_change", args=[obj.game.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.game.name)

    link_to_game.short_description = 'Game'

    def link_to_group(self, obj):
        link = reverse("admin:player_group_change", args=[obj.group.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.group.name)

    link_to_group.short_description = 'Group'

    def link_to_case(self, obj):
        link = reverse("admin:game_case_change", args=[obj.case.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.case.name)

    link_to_case.short_description = 'Case'


@admin.register(GroupArtifactInfo)
class GroupArtifactInfoAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = (
        'id', 'group_game_case_id', 'link_to_artifact', 'link_to_hidden_info', 'info_key', 'is_artifact_active')
    list_display_links = ('group_game_case_id',)
    search_fields = ('id',)

    def link_to_artifact(self, obj):
        link = reverse("admin:game_artifact_change", args=[obj.artifact.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.artifact.name)

    link_to_artifact.short_description = 'Artifact'

    def link_to_hidden_info(self, obj):
        link = reverse("admin:game_hiddeninfo_change", args=[obj.hidden_info.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.hidden_info.hiding_type.name)

    link_to_hidden_info.short_description = 'Hidden Info'


@admin.register(GroupResponse)
class GroupResponseAdmin(admin.ModelAdmin):
    readonly_fields = ('group_artifact_info',)
    list_display = ('group_artifact_info_id', 'response_date', 'score', 'player_comment', 'group_game_case_id')
    list_display_links = ('group_game_case_id', 'group_artifact_info_id')
    search_fields = ('group_artifact_info_id',)


@admin.register(GroupEvent)
class GroupEventAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'group_game_case_id', 'link_to_event', 'start_date', 'finish_date', 'is_active')
    list_display_links = ('group_game_case_id',)
    search_fields = ('id', 'event_id', 'event__name')

    def link_to_event(self, obj):
        link = reverse("admin:game_event_change", args=[obj.event.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.event.name)

    link_to_event.short_description = 'Event'


@admin.register(Character)
class CharacterAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'name', 'full_name', 'mail_address', 'link_to_case')
    search_fields = ('id', 'name', 'full_name')

    def link_to_case(self, obj):
        link = reverse("admin:game_case_change", args=[obj.case.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.case.name)

    link_to_case.short_description = 'Case'


@admin.register(CharacterEvent)
class CharacterEventAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'link_to_character', 'link_to_event')
    search_fields = ('id', 'character__name', 'event__name')

    def link_to_event(self, obj):
        link = reverse("admin:game_event_change", args=[obj.event.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.event.name)

    link_to_event.short_description = 'Event'

    def link_to_character(self, obj):
        link = reverse("admin:game_character_change", args=[obj.character.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.character.name)

    link_to_character.short_description = 'Character'


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'group_game_case_id', 'link_to_character', 'name')
    list_display_links = ('group_game_case_id',)
    search_fields = ('id', 'name')

    def link_to_character(self, obj):
        link = reverse("admin:game_character_change", args=[obj.character.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.character.name)

    link_to_character.short_description = 'Character'


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'group_game_case_id', 'link_to_contact', 'creation_date')
    list_display_links = ('group_game_case_id',)
    search_fields = ('id',)

    def link_to_contact(self, obj):
        link = reverse("admin:game_contact_change", args=[obj.contact.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{}</a>', link, obj.contact.name)

    link_to_contact.short_description = 'Contact'


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'date_message', 'story_message_id', 'unread_message', 'is_bot_message')
    list_display_links = ('story_message_id',)
    search_fields = ('id', 'date_message')
    


@admin.register(LearnActivity)
class LearnActivityAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'user', 'code', 'date','related','description')
    list_display_links = ('user',)
    search_fields = ('id', 'user','code')

@admin.register(Clue)
class ClueAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'hiddeninfo', 'order','clue_text','cost')
    list_display_links = ('hiddeninfo',)
    search_fields = ('id', 'hiddeninfo')
    
@admin.register(GroupClue)
class GroupClueAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'clue', 'group_artifact','available' )
    list_display_links = ('clue','group_artifact')
    search_fields = ('id','clue', 'group_artifact','available')    
