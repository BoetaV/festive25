# accounts/migrations/0002_create_superuser.py
from django.db import migrations
import os

def create_superuser(apps, schema_editor):
    # We get the User model for this historical version of the app
    User = apps.get_model('auth', 'User')
    
    # Get the superuser credentials from environment variables
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

    # Only proceed if all three variables are set
    if username and email and password:
        # Check if a user with that username already exists
        if not User.objects.filter(username=username).exists():
            # Create the superuser
            print(f"\nCreating superuser: {username}")
            User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            print("Superuser created successfully.")
        else:
            print(f"Superuser '{username}' already exists, skipping creation.")
    else:
        print("\nSuperuser environment variables not set, skipping superuser creation.")


class Migration(migrations.Migration):
    # This migration must run after the initial tables and groups are created
    dependencies = [
        ('accounts', '0001_initial'), 
    ]

    operations = [
        migrations.RunPython(create_superuser),
    ]
