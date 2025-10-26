#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Python packages
pip install -r requirements.txt

# Apply database migrations
# THIS COMMAND WILL RUN YOUR NEW SUPERUSER MIGRATION
python manage.py migrate

# Collect static files
python manage.py collectstatic --no-input

# (The gunicorn command is NOT here, it's in Render's "Start Command")