"""
Entry point for the Scimly backend.
Run with: uvicorn app.main:app --reload
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.session import Base, engine
from app.api import health, upload, dataset, dashboards, auth

# Import core models so SQLAlchemy knows about them before create_all()
from app.models import health as health_model  # noqa: F401
from app.models import file as file_model  # noqa: F401
from app.models import dataset as dataset_model  # noqa: F401
from app.models import user as user_model  # noqa: F401

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
Base.metadata.create_all(bind=engine)

# Register routes
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(dataset.router, prefix="/api", tags=["dataset"])
app.include_router(dashboards.router, prefix="/api", tags=["dashboards"])
app.include_router(auth.router, prefix="/api", tags=["auth"])


@app.get("/")
def root():
    return {"message": "Scimly API is running"}