import os
import sys
import django

# Add project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Set up Django environment early to avoid ImproperlyConfigured
os.environ["DJANGO_SETTINGS_MODULE"] = "core.settings"
django.setup()

# Now safe to import Django components and models
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User

def verify_pages():
    client = Client()
    
    # Create or get a superuser for testing
    username = "testadmin_verifier"
    password = "password123"
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email="admin@example.com", password=password)
    
    # Login
    if not client.login(username=username, password=password):
        print("Failed to login as superuser")
        return False

    pages_to_check = [
        ('dashboard', {}),
        ('admin:index', {}),
        ('session_history', {}),
        ('metrics', {}),
        ('monitor', {}),
        ('qr_dashboard', {}),
        ('admin:auth_user_changelist', {}),
        # Check User Change page for a specific user
        ('admin:auth_user_change', {'args': (User.objects.first().id,)}) if User.objects.exists() else None,
        # Check custom action (Change Password button) - should redirect (302) or exist
        ('admin:auth_user_change_password_custom', {'args': (User.objects.first().id,)}) if User.objects.exists() else None,
        # Check Quickfire Selector
        ('quickfire_selector', {}),
    ]

    success = True
    print("\n--- Verifying Application Pages ---")
    for page in pages_to_check:
        if page is None:
            continue
            
        url_name, kwargs = page
        try:
            url = reverse(url_name, **kwargs)
            response = client.get(url)
            if response.status_code in [200, 302]:
                print(f"[OK] {url_name} ({url}) - status {response.status_code}")
            else:
                print(f"[ERROR] {url_name} ({url}) returned status code {response.status_code}")
                success = False
        except Exception as e:
            print(f"[CRITICAL] Failed to access {url_name}: {str(e)}")
            success = False

    return success

if __name__ == "__main__":
    if verify_pages():
        print("\nAll key pages verified successfully.")
        sys.exit(0)
    else:
        print("\nPage verification failed.")
        sys.exit(1)
