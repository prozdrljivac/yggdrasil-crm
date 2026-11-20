"""Create the local JSON-only task worker without connecting to a broker."""

from celery import Celery

from src.config import Settings


def create_worker(settings: Settings) -> Celery:
    worker = Celery("yggdrasil_crm")
    worker.conf.update(
        broker_url=settings.broker_url.get_secret_value(),
        accept_content=["json"],
        task_serializer="json",
        result_serializer="json",
        task_ignore_result=True,
        broker_connection_retry_on_startup=True,
        worker_prefetch_multiplier=1,
    )
    return worker
