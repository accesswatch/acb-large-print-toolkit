"""WSGI entry point for Gunicorn."""

from .app import create_app

app = create_app()
