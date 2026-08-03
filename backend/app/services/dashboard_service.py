"""
Helpers backing the /api/dashboards routes (Phase 10).
"""
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.saved_dashboard import SavedDashboard


def get_or_create_user(db: Session, device_id: str) -> User:
    """Every browser gets one anonymous User row, keyed by a UUID it
    generates once and stores in localStorage (see the frontend's
    X-Device-Id header). Phase 12 can later attach an email to this
    same row once real login exists."""
    user = db.query(User).filter(User.device_id == device_id).first()
    if user:
        return user

    user = User(device_id=device_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_owned_dashboard(db: Session, dashboard_id: int, user_id: int) -> SavedDashboard | None:
    """Fetches a dashboard only if it belongs to this user — so one
    browser can never open, edit, or delete another's saved dashboard."""
    return (
        db.query(SavedDashboard)
        .filter(SavedDashboard.id == dashboard_id, SavedDashboard.user_id == user_id)
        .first()
    )
