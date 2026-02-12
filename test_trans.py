
import os
import django
from django.conf import settings
from django.utils import translation

# Minimal Django setup
if not settings.configured:
    settings.configure(
        USE_I18N=True,
        INSTALLED_APPS=['manager'],
        LOCALE_PATHS=[r'd:\net2000\locale'],
        LANGUAGE_CODE='ar',
        LANGUAGES=[('ar', 'Arabic'), ('en', 'English')],
    )
    django.setup()

translation.activate('ar')
print(f"Current language: {translation.get_language()}")
print(f"Translate 'Pay': {translation.gettext('Pay')}")
print(f"Translate 'Add': {translation.gettext('Add')}")
print(f"Translate 'Items': {translation.gettext('Items')}")
print(f"Translate 'Table': {translation.gettext('Table')}")
