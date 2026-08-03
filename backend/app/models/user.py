"""
Phase 10 gave us a very small User table keyed by an anonymous device id
(a UUID the frontend generates once and stores in localStorage, sent as
X-Device-Id). Phase 12 adds real identity on top of that same row:
email/password, or Google/GitHub OAuth. A row can have either, both, or
just a device_id — see app/api/deps.py for how a request resolves to
one of these.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from app.database.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Anonymous identity (Phase 10). Nullable because a user who only
    # ever registers with email/OAuth on a fresh browser has no device
    # id of their own — nullable + unique still allows any number of
    # NULLs in Postgres, so this doesn't collide across users.
    device_id = Column(String, nullable=True, unique=True, index=True)

    # Real identity (Phase 12).
    email = Column(String, nullable=True, unique=True, index=True)
    password_hash = Column(String, nullable=True)  # null for OAuth-only accounts
    name = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)

    # "email" | "google" | "github" — how this account was created.
    # An account can still end up with a password_hash *and* an OAuth
    # id if the person later links a provider to an email/password
    # account (or vice versa), so treat this as "how they signed up",
    # not "the only way they can log in".
    auth_provider = Column(String, nullable=True, default="email")
    google_id = Column(String, nullable=True, unique=True, index=True)
    github_id = Column(String, nullable=True, unique=True, index=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
