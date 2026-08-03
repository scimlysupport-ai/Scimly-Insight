"""
GET /api/health -> confirms the API is running and can talk to Postgres.
This is the very first thing we'll test once everything is running.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import get_db

router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "api": "running",
        "database": "connected",
    }
