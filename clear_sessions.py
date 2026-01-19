import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.sessions.models import Session
Session.objects.all().delete()
print("All sessions cleared. Users will need to log in again.")
