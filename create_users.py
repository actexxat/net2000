import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User

# List of usernames to create
usernames = [str(i) for i in range(1, 11)]

for username in usernames:
    password = username * 4
    if not User.objects.filter(username=username).exists():
        User.objects.create_user(username=username, password=password)
        print(f"Created user: {username} with password: {password}")
    else:
        # Update existing user password
        u = User.objects.get(username=username)
        u.set_password(password)
        u.save()
        print(f"Updated password for user: {username} to: {password}")

print("User creation/update complete.")
