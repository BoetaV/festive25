# Use Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /app/

# Run collectstatic (if applicable)
RUN python manage.py collectstatic --noinput || true

# Expose port
EXPOSE 8000

# Start server
CMD ["gunicorn", "festive.wsgi:application", "--bind", "0.0.0.0:8000"]
