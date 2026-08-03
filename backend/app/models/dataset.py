"""
Stores the analysis result (metadata/schema/stats) for an uploaded file.
One UploadedFile -> one Dataset, created once analysis finishes.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from app.database.session import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("uploaded_files.id"), nullable=False, unique=True)
    rows = Column(Integer, nullable=False)
    columns = Column(Integer, nullable=False)
    schema_json = Column(JSON, nullable=False)  # list of {name, dtype, stats}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
