# Celery app instance — Redis as broker and result backend.
#
# Nothing calls .delay()/.apply_async() on these tasks yet (see extract_document.py's
# module docstring for why); this app exists so that switch is a one-line change once
# Redis is actually running, without having to restructure the task functions.

from celery import Celery

from app.config import settings

celery_app = Celery("iso_certification", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
