from django import template
from game.business import GroupGameCaseBusiness, GroupEventBusiness

register = template.Library()


@register.simple_tag(takes_context=True)
def status_like_icon_class(context, group_artifact_info):
    request = context['request']
    user_id = request.user.id
    if group_artifact_info.groupresponse.playerrating_set.filter(player_id=user_id).exists():
        return "fas"
    else:
        return "far"

