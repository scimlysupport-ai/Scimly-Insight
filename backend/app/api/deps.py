"""
Phase 12 — one dependency used by every route that needs to know "who is
asking": upload, dataset, and dashboards all switch from the old
device-id-only check to this. It prefers a real login (Authorization:
Bearer <jwt>) and falls back to the Phase 10 anonymous X-Device-Id
header, so nothing that worked before Phase 12 breaks for someone who
never creates an account.
"""
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.services.auth_service import decode_access_token
from app.services.dashboard_service import get_or_create_user


def get_current_user(
    authorization: str | None = Header(default=None),
    x_device_id: str | None = Header(default=None, alias="X-Device-Id"),
    db: Session = Depends(get_db),
) -> User:
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[len("bearer "):].strip()
        user_id = decode_access_token(token)
        if user_id is None:
            raise HTTPException(status_code=401, detail="Session expired or invalid — please log in again.")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="Session expired or invalid — please log in again.")
        return user

    if not x_device_id:
        raise HTTPException(
            status_code=400,
            detail="Missing X-Device-Id header — required when not logged in.",
        )
    return get_or_create_user(db, x_device_id)


def get_current_user_id(user: User = Depends(get_current_user)) -> int:
    return user.id
