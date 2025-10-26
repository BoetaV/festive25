#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Python dependencies from requirements.txt
pip install -r requirements.txt

# Apply database migrations for your apps (creates User, Profile, Delivery tables, etc.)
python manage.py migrate

# --- THIS IS THE NEW, CRITICAL COMMAND ---
# Create the database table needed for Django's database cache backend.
python manage.py createcachetable

# Create the superuser from environment variables
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
import os
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
if username and email and password and not User.objects.filter(username=username).exists():
    print("Creating superuser...")
    User.objects.create_superuser(username=username, email=email, password=password)
else:
    print("Superuser already exists or credentials not set, skipping.")
EOF

# Collect static files for Whitenoise to serve
python manage.py collectstatic --no-input