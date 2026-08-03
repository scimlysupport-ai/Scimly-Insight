"""
A tiny placeholder model just to prove the database connection works
in Phase 1. Real models (File, Dataset, Dashboard, Widget...) get added
in later phases.
"""
from sqlalchemy import Column, Integer, String
from app.database.session import Base


class HealthCheck(Base):
    __tablename__ = "health_check"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="ok")
