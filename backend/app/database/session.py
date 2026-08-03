"""
Sets up the SQLAlchemy engine and session factory.
Every API route that needs the database will use `get_db()` below.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency: gives each request its own DB session
    and closes it automatically when the request is done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
