"""
Represents a connected live data source.
Live sources let users build dashboards directly from databases, APIs,
Google Sheets, or MongoDB without uploading a local CSV/Excel file.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from app.database.session import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    source_type = Column(String, nullable=False, index=True)
    config_json = Column(JSON, nullable=False)
    status = Column(String, default="ready")  # ready | processing | failed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
