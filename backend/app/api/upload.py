"""
POST /api/upload      -> upload a CSV/XLSX file, returns { id: 123 }
GET  /api/uploads      -> list recent uploads (for the "Recent Uploads" UI panel)
DELETE /api/uploads/{file_id} -> delete an uploaded file and its analysis

Phase 12 — uploads now belong to whoever uploaded them (a real logged-in
user or an anonymous device id — see app/api/deps.py), so "recent
uploads" and delete are scoped per user instead of listing everyone's
files.

Phase 13 — files at/above LARGE_FILE_THRESHOLD_BYTES are queued for
background analysis (a Celery task) right here at upload time, instead
of waiting for the first GET /dataset/{file_id} call to discover the
file is huge and block a request thread on it.
"""
import logging
import os

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.database.session import get_db
from app.models.dataset import Dataset
from app.models.file import UploadedFile
from app.schemas.file import UploadedFileResponse
from app.services.file_service import (
    UPLOAD_DIR,
    validate_file_basic,
    validate_file_readable,
    save_upload,
    is_large_file,
)
from app.services.progress_service import set_progress
from app.workers.tasks import process_large_file

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=UploadedFileResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    file_bytes = await file.read()

    extension = validate_file_basic(file, file_bytes)
    stored_filename, full_path = save_upload(file_bytes, extension)
    validate_file_readable(full_path, extension)

    size_bytes = len(file_bytes)
    large = is_large_file(size_bytes)

    db_file = UploadedFile(
        user_id=user_id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_extension=extension,
        size_bytes=size_bytes,
        status="processing" if large else "uploaded",
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)

    if large:
        set_progress(db_file.id, "queued", 0, "Waiting for a worker to pick this up…")
        try:
            process_large_file.apply_async(args=[db_file.id], queue="celery")
        except Exception as exc:
            logger.exception("Failed to enqueue Celery task for file %s", db_file.id)
            db_file.status = "failed"
            db.commit()
            set_progress(db_file.id, "failed", 0, "Could not queue background analysis.")
            raise HTTPException(
                status_code=500,
                detail="Failed to queue background analysis. Please retry."
            ) from exc

    return db_file


@router.get("/uploads", response_model=list[UploadedFileResponse])
def list_uploads(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return (
        db.query(UploadedFile)
        .filter(UploadedFile.user_id == user_id)
        .order_by(UploadedFile.created_at.desc())
        .limit(20)
        .all()
    )


@router.delete("/uploads/{file_id}", status_code=204)
def delete_upload(
    file_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    file_record = (
        db.query(UploadedFile)
        .filter(UploadedFile.id == file_id, UploadedFile.user_id == user_id)
        .first()
    )
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found.")

    dataset = db.query(Dataset).filter(Dataset.file_id == file_id).first()
    if dataset:
        db.delete(dataset)

    full_path = os.path.join(UPLOAD_DIR, file_record.stored_filename)
    if os.path.exists(full_path):
        os.remove(full_path)

    db.delete(file_record)
    db.commit()
    return None
