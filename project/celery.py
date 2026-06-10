import os
from celery import Celery

# Ensure a sensible default settings module exists in this project
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings.base')

app = Celery('project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

__all__ = ('app',)
