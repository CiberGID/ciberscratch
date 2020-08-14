from django.contrib import admin
from django.utils import html
from django.urls import reverse
from .models import Department, Course, Group, UserGroup


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'name', 'url')
    search_fields = ('name',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    readonly_fields = ('id',)
    list_display = ('id', 'name', 'department')
    search_fields = ('name',)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'year', 'enabled')
    search_fields = ('name',)


@admin.register(UserGroup)
class UserGroupAdmin(admin.ModelAdmin):
    list_display = ('player', 'link_group')
    search_fields = ('player',)

    def link_group(self, obj):
        link = reverse("admin:player_group_change", args=[obj.group.id])  # model name has to be lowercase
        return html.format_html('<a href="{}">{} - ({} {})</a>', link, obj.group.name, obj.group.course, obj.group.year)

    link_group.short_description = 'Group'
