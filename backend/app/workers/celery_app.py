from celery import Celery

from app.config import settings

celery_app = Celery("ai_code_reviewer", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    task_track_started=True,
)
celery_app.autodiscover_tasks(["app.workers"])
