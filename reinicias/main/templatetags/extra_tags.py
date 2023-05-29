from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def has_group(value,arg):
    return value.filter(name=arg).exists()

@register.filter
def get_item(value,arg):
    return value.get(arg)