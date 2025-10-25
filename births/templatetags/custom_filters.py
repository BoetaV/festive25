# births/templatetags/custom_filters.py

from django import template
from django.core.cache import cache
from django.contrib.auth.models import User

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Allows accessing a dictionary key with a variable in Django templates."""
    return dictionary.get(key)

@register.simple_tag
def get_active_users():
    """
    Gets a list of all user IDs from the cache that have been active recently.
    This is an optimized version.
    """
    all_user_ids = User.objects.filter(is_superuser=False).values_list('id', flat=True)
    cache_keys = [f'last-seen-{user_id}' for user_id in all_user_ids]
    found_caches = cache.get_many(cache_keys)
    active_user_ids = [int(key.split('-')[-1]) for key in found_caches.keys()]
    return User.objects.filter(id__in=active_user_ids).select_related('profile')