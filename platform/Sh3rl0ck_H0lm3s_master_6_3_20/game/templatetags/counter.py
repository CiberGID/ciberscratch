from django import template
from game.business import GroupGameCaseBusiness, GroupEventBusiness

register = template.Library()


@register.filter
def count_complete_missions(ggc):
    return GroupGameCaseBusiness.count_complete_missions(group_game_case_id=ggc.id)


@register.filter
def count_hidden_info_founded(group_event):
    return GroupEventBusiness.count_hidden_info_founded(group_event_id=group_event.id)


@register.filter
def sum_group_event_score(group_event):
    return GroupEventBusiness.sum_group_event_score(group_event_id=group_event.id)
