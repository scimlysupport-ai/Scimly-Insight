"""
Response shapes for the /upload endpoints. Keeping these separate from
the SQLAlchemy model means the API response format can evolve without
touching the database schema.
"""
from datetime import datetime
from pydantic import BaseModel


class UploadedFileResponse(BaseModel):
    id: int
    original_filename: str
    size_bytes: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class UploadErrorResponse(BaseModel):
    detail: str
