import os
import sys
import django
from django.core.management import call_command

# Add current directory to path
sys.path.append(os.getcwd())

# Set settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Initialize django
django.setup()

# Run collectstatic
call_command('collectstatic', interactive=False)
print("Static files collected successfully.")
