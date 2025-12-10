# births/templatetags/custom_filters.py

from django import template
from django.core.cache import cache
from django.contrib.auth.models import User

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Allows accessing a dictionary key with a variable in Django templates."""
    return dictionary.get(key)
