"""
Phase 13 — background analysis task for large uploads.

This is the same Read -> Clean -> Detect types -> Generate stats pipeline
GET /dataset/{file_id} runs synchronously for small files (app/api/dataset.py,
Phase 3), just run from a Celery worker instead of a request thread, with
progress checkpoints written to Redis along the way.

Runs in its own OS process, separate from the FastAPI app, so it needs its
own DB session — it can't borrow the one from a request's get_db().
"""
import os

from app.database.session import SessionLocal
from app.models import dataset  # noqa: F401
from app.models import file  # noqa: F401
from app.models import user  # noqa: F401
from app.models.dataset import Dataset
from app.models.file import UploadedFile
from app.services.analysis_service import analyze_dataframe, read_dataframe
from app.services.file_service import UPLOAD_DIR
from app.services.progress_service import set_progress
from app.workers.celery_app import app


@app.task(name="app.workers.tasks.process_large_file", bind=True, max_retries=0)
def process_large_file(self, file_id: int) -> dict:
    db = SessionLocal()
    try:
        file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not file_record:
            # The upload row disappeared (e.g. deleted mid-queue) — nothing
            # to process, and nothing to mark failed either.
            set_progress(file_id, "failed", 0, "File record no longer exists.")
            return {"ok": False, "reason": "file_not_found"}

        full_path = os.path.join(UPLOAD_DIR, file_record.stored_filename)
        if not os.path.exists(full_path):
            file_record.status = "failed"
            db.commit()
            set_progress(file_id, "failed", 0, "Stored file is missing on disk.")
            return {"ok": False, "reason": "file_missing_on_disk"}

        set_progress(file_id, "reading", 10, "Reading file…")
        df = read_dataframe(full_path, file_record.file_extension)

        set_progress(file_id, "cleaning", 40, "Cleaning and deduplicating…")
        # analyze_dataframe does its own dedup internally, but for a large
        # file the read -> dedup gap is where most of the wall-clock time
        # goes, so it earns its own progress checkpoint even though the
        # actual dedup call happens inside the next stage.

        set_progress(file_id, "analyzing", 65, "Detecting column types and computing statistics…")
        result = analyze_dataframe(df)

        set_progress(file_id, "saving", 90, "Saving results…")
        existing = db.query(Dataset).filter(Dataset.file_id == file_id).first()
        if existing:
            existing.rows = result["rows"]
            existing.columns = result["columns"]
            existing.schema_json = result["schema"]
        else:
            db.add(
                Dataset(
                    file_id=file_id,
                    rows=result["rows"],
                    columns=result["columns"],
                    schema_json=result["schema"],
                )
            )
        file_record.status = "ready"
        db.commit()

        set_progress(file_id, "ready", 100, "Analysis complete.")
        return {"ok": True, "rows": result["rows"], "columns": result["columns"]}

    except Exception as exc:
        db.rollback()
        file_record = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if file_record:
            file_record.status = "failed"
            db.commit()
        set_progress(file_id, "failed", 0, f"Analysis failed: {exc}")
        # Not re-raised: task_acks_late means an uncaught exception here
        # would get the (already-failed) job redelivered to another
        # worker and retried forever, since max_retries=0 still leaves
        # Celery's own crash-redelivery in play — an analysis failure
        # (bad data) isn't a transient worker fault and won't succeed on
        # retry, so surface it via `status`/Redis instead of the task's
        # exception state.
        return {"ok": False, "reason": str(exc)}
    finally:
        db.close()
