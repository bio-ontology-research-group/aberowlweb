from __future__ import absolute_import, unicode_literals

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from celery import Celery

celery_app = Celery('aberowlweb')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
celery_app.config_from_object('django.conf:settings', namespace='CELERY')
# Load task modules from all registered Django app configs.
celery_app.autodiscover_tasks()

__all__ = ['celery_app']
