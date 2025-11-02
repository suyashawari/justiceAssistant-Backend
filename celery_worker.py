"""
Celery worker entry point.
This file creates the Flask app and exposes the Celery instance
for the Celery worker to use.

Usage:
    celery -A celery_worker worker --loglevel=info
"""
from app.models import create_app

# Create the Flask application
flask_app = create_app()

# Extract the Celery app from Flask extensions
celery_app = flask_app.extensions["celery"]