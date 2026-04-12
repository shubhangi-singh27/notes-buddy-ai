import os
from celery import Celery
from celery.signals import setup_logging

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "notes_buddy.settings")

app = Celery("notes_buddy")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

@setup_logging.connect
def configure_django_logging(**kwargs):
    from django.conf import settings
    from logging.config import dictConfig
    dictConfig(settings.LOGGING)