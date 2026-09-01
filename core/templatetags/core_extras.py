from django import template

from core.permissions import can_view_dashboard as _can_view_dashboard

register = template.Library()


@register.filter
def can_view_dashboard(user):
    return _can_view_dashboard(user)
