"""
All the business logic for handling an uploaded file:
validating it, saving it to disk with a safe unique name, and
confirming it's actually readable as a dataset (not just correctly named).
"""
import os
import uuid
import pandas as pd
from fastapi import UploadFile, HTTPException

from app.config import settings

ALLOWED_EXTENSIONS = {".csv", ".xlsx"}
# Phase 13 raised the hard cap from Phase 2's flat 50MB — anything up to
# MAX_FILE_SIZE_BYTES is now accepted, and anything at/above
# LARGE_FILE_THRESHOLD_BYTES is routed to the background Celery pipeline
# instead of being analyzed inline on first request.
MAX_FILE_SIZE_BYTES = settings.MAX_FILE_SIZE_BYTES
LARGE_FILE_THRESHOLD_BYTES = settings.LARGE_FILE_THRESHOLD_BYTES

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads")
UPLOAD_DIR = os.path.abspath(UPLOAD_DIR)


def is_large_file(size_bytes: int) -> bool:
    return size_bytes >= LARGE_FILE_THRESHOLD_BYTES


def _get_extension(filename: str) -> str:
    _, ext = os.path.splitext(filename)
    return ext.lower()


def validate_file_basic(file: UploadFile, file_bytes: bytes) -> str:
    """Checks extension, empty-file, and size. Returns the validated extension."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    extension = _get_extension(file.filename)
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{extension}'. Only .csv and .xlsx are supported.",
        )

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File is too large. Maximum allowed size is {max_mb} MB.",
        )

    return extension


def validate_file_readable(saved_path: str, extension: str) -> None:
    """
    Confirms the file can actually be parsed as tabular data
    (catches corrupted files, wrong-content-with-right-extension, etc.)
    """
    try:
        if extension == ".csv":
            pd.read_csv(saved_path, nrows=5)
        else:
            pd.read_excel(saved_path, nrows=5)
    except Exception as exc:
        os.remove(saved_path)
        raise HTTPException(
            status_code=400,
            detail=f"File could not be read as valid {extension} data: {exc}",
        )


def save_upload(file_bytes: bytes, extension: str) -> tuple[str, str]:
    """Saves the file to disk with a unique name. Returns (stored_filename, full_path)."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    stored_filename = f"{uuid.uuid4().hex}{extension}"
    full_path = os.path.join(UPLOAD_DIR, stored_filename)

    with open(full_path, "wb") as f:
        f.write(file_bytes)

    return stored_filename, full_path
