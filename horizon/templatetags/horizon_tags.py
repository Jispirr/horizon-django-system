from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Get an item from a dict using a template variable as key."""
    try:
        return dictionary.get(int(key), 0)
    except (TypeError, ValueError):
        return dictionary.get(key, 0)


@register.filter(name='dict_get')
def dict_get(dictionary, key):
    """Get a value from a QueryDict or dict by key (used in admin change_list)."""
    if hasattr(dictionary, 'get'):
        return dictionary.get(key, '')
    return ''


@register.filter(name='class_name')
def class_name(obj):
    """Return the class name of an object — used in admin change_list filters."""
    return obj.__class__.__name__
