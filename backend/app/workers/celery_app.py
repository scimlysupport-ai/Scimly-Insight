"""
Phase 13 — the Celery application instance.

Run the worker from backend/ with:
    celery -A app.workers.celery_app worker --loglevel=info

Uses Redis as both broker (queues the task) and result backend (stores
the task's return value/state) — no extra infrastructure beyond the
Redis container already added to docker-compose for this phase.

Tasks are registered via `include=` rather than importing app.workers.tasks
directly in this module: tasks.py needs the Celery `app` instance itself
(for the @app.task decorator), so a top-level `from app.workers import
tasks` here would import tasks.py before this module finishes defining
`app`, and tasks.py's `from app.workers.celery_app import app` would
receive a half-initialized module. `include` defers that import until
Celery is ready to resolve it.
"""
from celery import Celery
from kombu import Queue

from app.config import settings

app = Celery(
    "scimly",
    broker=settings.REDIS_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_default_queue="celery",
    task_queues=[Queue("celery")],
    # A worker that dies mid-file leaves the task "reserved" but not
    # acked unless we're careful here; late ack means the task is only
    # marked done *after* it finishes, so a crashed worker's in-progress
    # large-file job gets redelivered to another worker instead of
    # silently vanishing.
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
