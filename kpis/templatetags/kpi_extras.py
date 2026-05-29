from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Allows accessing a dictionary value by key in a template."""
    return dictionary.get(key)