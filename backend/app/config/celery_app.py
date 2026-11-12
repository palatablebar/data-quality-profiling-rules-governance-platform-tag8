"""Celery application used by backend (producer) and worker (consumer)."""
from celery import Celery

from app.config.settings import settings

celery_app = Celery(
    "qualiscope",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.profile_dataset",
        "app.tasks.execute_rules",
        "app.tasks.recheck_issues",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=False,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    worker_hijack_root_logger=False,
    task_acks_late=False,
)

# aliases so `celery -A app.config.celery_app worker` resolves under every
# celery discovery convention (app / celery / celery_app attribute)
app = celery_app
celery = celery_app
