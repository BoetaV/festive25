# births/templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Allows accessing a dictionary key with a variable in Django templates.
    Usage: {{ my_dict|get_item:my_variable_key }}
    """
    return dictionary.get(key)