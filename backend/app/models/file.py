"""
Represents one uploaded file. The actual bytes live on disk in /uploads,
this table just tracks metadata about it.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database.session import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)
    # Phase 12 — every upload now belongs to whoever uploaded it (an
    # anonymous device-id user or a logged-in one — see app/api/deps.py).
    # Nullable so any pre-Phase-12 rows in an existing dev database don't
    # break; new uploads always set this.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False, unique=True)
    file_extension = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    status = Column(String, default="uploaded")  # uploaded | processing | ready | failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
