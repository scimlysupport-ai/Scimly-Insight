"""
Phase 12 — Authentication.

Everything that isn't route-plumbing lives here:
 - password hashing/verification (bcrypt)
 - issuing and decoding JWT access tokens
 - looking up/creating a User for Google or GitHub OAuth
 - "claiming" an anonymous device's uploads/dashboards onto a real
   account the first time that device registers or logs in, so nobody
   loses the work they did before creating an account.
"""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.models.file import UploadedFile
from app.models.saved_dashboard import SavedDashboard


# ---------------------------------------------------------------------------
# Passwords
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        # Malformed/empty hash (e.g. an OAuth-only account) — never a match.
        return False


# ---------------------------------------------------------------------------
# JWTs
# ---------------------------------------------------------------------------

def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expires_at}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """Returns the user id encoded in the token, or None if it's missing,
    expired, or was signed with a different secret."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Registration / login
# ---------------------------------------------------------------------------

def register_user(db: Session, email: str, password: str, name: str | None) -> User:
    user = User(
        email=email,
        password_hash=hash_password(password),
        name=name,
        auth_provider="email",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.password_hash:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


# ---------------------------------------------------------------------------
# OAuth (Google / GitHub)
# ---------------------------------------------------------------------------

def get_or_create_oauth_user(
    db: Session,
    provider: str,
    provider_user_id: str,
    email: str | None,
    name: str | None,
    avatar_url: str | None,
) -> User:
    """Finds the User for this provider account, creating one if this is
    the first time we've seen it. If an email/password (or other
    provider) account already exists with the same email, that account
    is reused and linked rather than creating a duplicate — so someone
    who registered with email can also click "Log in with Google" later
    using the same address."""
    id_column = User.google_id if provider == "google" else User.github_id
    user = db.query(User).filter(id_column == provider_user_id).first()
    if user:
        return user

    user = db.query(User).filter(User.email == email).first() if email else None
    if user:
        if provider == "google":
            user.google_id = provider_user_id
        else:
            user.github_id = provider_user_id
        user.avatar_url = user.avatar_url or avatar_url
        db.commit()
        db.refresh(user)
        return user

    user = User(
        email=email,
        name=name,
        avatar_url=avatar_url,
        auth_provider=provider,
        google_id=provider_user_id if provider == "google" else None,
        github_id=provider_user_id if provider == "github" else None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# Anonymous -> real account migration
# ---------------------------------------------------------------------------

def claim_device_data(db: Session, real_user: User, device_id: str | None) -> None:
    """When someone registers or logs in from a browser that already has
    an anonymous device-id user with uploads/dashboards, move that data
    onto the real account instead of leaving it stranded — as long as
    the device isn't already tied to a *different* real account."""
    if not device_id:
        return

    device_user = db.query(User).filter(User.device_id == device_id).first()
    if not device_user or device_user.id == real_user.id:
        return
    if device_user.email or device_user.google_id or device_user.github_id:
        # This device id belongs to someone else's real account —
        # never merge two identities together.
        return

    db.query(UploadedFile).filter(UploadedFile.user_id == device_user.id).update(
        {"user_id": real_user.id}
    )
    db.query(SavedDashboard).filter(SavedDashboard.user_id == device_user.id).update(
        {"user_id": real_user.id}
    )
    db.delete(device_user)
    db.commit()
