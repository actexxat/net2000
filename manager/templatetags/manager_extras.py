from django import template
from django.utils.translation import get_language, gettext as _

register = template.Library()

@register.filter
def translate_numbers(value):
    if get_language() != 'ar':
        return value
    
    arabic_numbers = '٠١٢٣٤٥٦٧٨٩'
    english_numbers = '0123456789'
    
    translation_table = str.maketrans(english_numbers, arabic_numbers)
    return str(value).translate(translation_table)

import re

@register.filter
def translate_text(value):
    if not value:
        return value
    
    text = str(value)
    is_ar = get_language() == 'ar'
    
    # Handle comma separated lists (summary field)
    if ", " in text:
        parts = text.split(", ")
        translated_parts = [translate_text(p) for p in parts]
        return ", ".join(translated_parts)
    
    # Handle [...] suffix (notes in history summary)
    bracket_note = ""
    if " [" in text and text.endswith("]"):
        start = text.rfind(" [") # use rfind to catch the last one
        bracket_note = text[start:]
        text = text[:start]
    
    # Handle suffixes like (Single) and (Double)
    suffix = ""
    if " (Single)" in text:
        suffix = " (عادي)" if is_ar else " (Single)"
        text = text.replace(" (Single)", "")
    elif " (Double)" in text:
        suffix = " (دوبل)" if is_ar else " (Double)"
        text = text.replace(" (Double)", "")
        
    translated = _(text)
    
    return f"{translated}{suffix}{bracket_note}"
    
@register.simple_tag
def get_shift_status():
    from manager.models import GlobalSettings
    settings, _ = GlobalSettings.objects.get_or_create(id=1)
    return settings.active_shift
