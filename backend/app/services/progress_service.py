"""
Phase 13 — tracks background-processing progress for large uploaded files.

Analysis of a large file happens inside a Celery worker process, not the
FastAPI request/response cycle, so there's no request left to report
progress on. The worker writes progress into Redis as it moves through
the pipeline; the frontend polls GET /dataset/{file_id}/progress, which
just reads whatever the worker last wrote.

Keyed by file_id rather than task_id: the frontend already knows the
file_id (it's the id returned from POST /upload) and never sees or needs
a Celery task id.
"""
import json
import logging
from datetime import timedelta

import redis

from app.config import settings

logger = logging.getLogger(__name__)

_redis_client: redis.Redis | None = None

PROGRESS_TTL = timedelta(hours=6)

VALID_STAGES = {"queued", "reading", "cleaning", "analyzing", "saving", "ready", "failed"}


def _key(file_id: int) -> str:
    return f"scimly:progress:{file_id}"


def get_redis() -> redis.Redis:
    """Lazily creates a single shared Redis connection (pool) per process."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client


def set_progress(file_id: int, stage: str, percent: int, message: str | None = None) -> None:
    """Overwrites the current progress snapshot for a file."""
    if stage not in VALID_STAGES:
        raise ValueError(f"Unknown progress stage '{stage}'. Must be one of {VALID_STAGES}.")

    payload = {
        "status": stage,
        "progress": max(0, min(100, int(percent))),
        "message": message,
    }
    try:
        client = get_redis()
        client.set(_key(file_id), json.dumps(payload), ex=PROGRESS_TTL)
    except Exception as exc:
        logger.warning("Redis set_progress failed (Redis offline?): %s", exc)


def get_progress(file_id: int) -> dict | None:
    """Returns the last-written progress snapshot, or None if Redis is unavailable/empty."""
    try:
        client = get_redis()
        raw = client.get(_key(file_id))
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.warning("Redis get_progress failed (Redis offline?): %s", exc)
        return None


def clear_progress(file_id: int) -> None:
    """Removes the progress key once it's no longer needed."""
    try:
        get_redis().delete(_key(file_id))
    except Exception as exc:
        logger.warning("Redis clear_progress failed: %s", exc)
