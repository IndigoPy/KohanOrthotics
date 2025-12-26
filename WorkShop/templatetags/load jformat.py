from django import template
from django_jalali.templatetags import jformat

register = template.Library()


@register.filter(name='to_jalali')
def to_jalali_filter(value, date_format):
    return jformat(value, date_format)
