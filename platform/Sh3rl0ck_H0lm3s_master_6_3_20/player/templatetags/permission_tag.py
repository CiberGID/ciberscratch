from django import template

register = template.Library()


@register.filter
def check_permission(user, permission):
    return user.has_perm(permission)
