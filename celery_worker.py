#!/usr/bin/env python

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
import configurations
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aberowlweb.settings')
os.environ.setdefault('DJANGO_CONFIGURATION', 'Production')

configurations.setup()

app = Celery('aberowlweb')

# Using a string here means the worker don't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object(settings, namespace='CELERY')
# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Start worker
app.worker_main(['worker', '-l=INFO', '-B'])