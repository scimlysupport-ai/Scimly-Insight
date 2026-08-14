"""
Entry point for the Scimly backend.
Run with: uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from sqlalchemy import inspect, text
from app.database.session import Base, engine
from app.api import health, upload, dataset, dashboards, auth, datasources, enterprise

# Import core models so SQLAlchemy knows about them before create_all()
from app.models import health as health_model  # noqa: F401
from app.models import file as file_model  # noqa: F401
from app.models import dataset as dataset_model  # noqa: F401
from app.models import data_source as data_source_model  # noqa: F401
from app.models import user as user_model  # noqa: F401
from app.models import enterprise as enterprise_model  # noqa: F401

app = FastAPI(title="Scimly API", version="0.1.0")

# Allow the React frontend (running on a different port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables on startup (fine for dev; a real migration tool
# like Alembic is worth introducing before this ships to production, since
# create_all() only ever adds new tables — it won't alter an existing one
# if a column changes later)
if settings.APP_ENV == "development":
    Base.metadata.create_all(bind=engine)

    # Ensure the development SQLite schema is up-to-date for the new datasource
    # column, and the new enterprise role column, since this repo is using
    # create_all() rather than a full migration tool yet.
    inspector = inspect(engine)
    if inspector.has_table("datasets"):
        columns = {col["name"] for col in inspector.get_columns("datasets")}
        if "datasource_id" not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE datasets ADD COLUMN datasource_id INTEGER"))
                conn.commit()

    if inspector.has_table("users"):
        columns = {col["name"] for col in inspector.get_columns("users")}
        if "role" not in columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'member'"))
                conn.commit()

# Register routes
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(dataset.router, prefix="/api", tags=["dataset"])
app.include_router(dashboards.router, prefix="/api", tags=["dashboards"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(datasources.router, prefix="/api", tags=["datasources"])
app.include_router(enterprise.router, prefix="/api", tags=["enterprise"])


@app.get("/")
def root():
    return {"message": "Scimly API is running"}