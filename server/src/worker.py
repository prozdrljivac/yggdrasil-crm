"""Celery entry point. Supply the development environment before importing."""

from src.background import create_worker
from src.config import Settings

app = create_worker(Settings())
