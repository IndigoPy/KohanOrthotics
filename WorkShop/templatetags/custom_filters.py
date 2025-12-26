# یک تمپلیت تگ در یک فایل templatetags بنویسیم
from django import template
from django_jalali.templatetags import jformat

register = template.Library()


@register.filter
def translate_status(value):
    translations = {
        "in_progress": "در حال ساخت",
        "ready": "آماده تحویل",
        "delivered": "تحویل داده شده"
    }
    return translations.get(value, value)



