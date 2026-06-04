from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "wexaai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.event_tasks",
        "app.tasks.alert_tasks",
        "app.tasks.report_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_max_retries=3,
    task_default_retry_delay=60,
    result_expires=3600,
    # Beat schedule for periodic tasks
    beat_schedule={
        "evaluate-alerts-every-minute": {
            "task": "app.tasks.alert_tasks.evaluate_all_alerts",
            "schedule": crontab(minute="*"),  # every minute
        },
        "run-scheduled-reports": {
            "task": "app.tasks.report_tasks.run_scheduled_reports",
            "schedule": crontab(minute="*/5"),  # every 5 minutes
        },
    },
)
