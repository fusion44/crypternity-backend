from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
app = Celery("backend")

app.config_from_object("django.conf:settings", namespace='CELERY')

app.autodiscover_tasks()

app.conf.beat_schedule = {
    'update-coins-every-24-hours': {
        'task': 'backend.coins.tasks.async_update_supported_coins',
        'schedule': 86400.0,  # 24 hours
        'options': {
            'task_id': "task_update_coins"
        },
    },
}
