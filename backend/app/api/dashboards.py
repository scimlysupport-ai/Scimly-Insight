"""
Phase 10 — Save Dashboard.

POST   /api/dashboards                 -> save a new dashboard
GET    /api/dashboards?file_id=        -> list this user's saved dashboards
GET    /api/dashboards/{id}            -> open one (widgets + layout + filters)
PUT    /api/dashboards/{id}            -> save changes to an existing one
POST   /api/dashboards/{id}/duplicate  -> duplicate
DELETE /api/dashboards/{id}            -> delete

Every route requires either a logged-in session (Authorization: Bearer
<jwt>) or the anonymous X-Device-Id header, resolved by the shared
get_current_user_id dependency (Phase 12 — see app/api/deps.py).
"Ownership" means "created by this real user, or this browser's device
id if nobody's logged in".
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.database.session import get_db
from app.models.file import UploadedFile
from app.models.saved_dashboard import SavedDashboard
from app.schemas.dashboard import (
    SavedDashboardCreate,
    SavedDashboardUpdate,
    SavedDashboardDuplicate,
    SavedDashboardResponse,
    SavedDashboardSummary,
)
from app.services.dashboard_service import get_owned_dashboard

router = APIRouter()


@router.post("/dashboards", response_model=SavedDashboardResponse)
def create_dashboard(
    payload: SavedDashboardCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    file_record = db.query(UploadedFile).filter(UploadedFile.id == payload.file_id).first()
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found.")

    dashboard = SavedDashboard(
        user_id=user_id,
        file_id=payload.file_id,
        name=payload.name or "Untitled dashboard",
        widgets_json=[w.model_dump() for w in payload.widgets],
        layout_json=[l.model_dump() for l in payload.layout],
        filters_json=payload.filters.model_dump(),
    )
    db.add(dashboard)
    db.commit()
    db.refresh(dashboard)
    return SavedDashboardResponse.from_model(dashboard)


@router.get("/dashboards", response_model=list[SavedDashboardSummary])
def list_dashboards(
    file_id: int | None = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    query = db.query(SavedDashboard).filter(SavedDashboard.user_id == user_id)
    if file_id is not None:
        query = query.filter(SavedDashboard.file_id == file_id)
    dashboards = query.order_by(SavedDashboard.updated_at.desc()).all()

    file_ids = {d.file_id for d in dashboards}
    files_by_id = {
        f.id: f.original_filename
        for f in db.query(UploadedFile).filter(UploadedFile.id.in_(file_ids)).all()
    }

    return [
        SavedDashboardSummary.from_model(d, file_name=files_by_id.get(d.file_id))
        for d in dashboards
    ]


@router.get("/dashboards/{dashboard_id}", response_model=SavedDashboardResponse)
def get_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    dashboard = get_owned_dashboard(db, dashboard_id, user_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Saved dashboard not found.")
    return SavedDashboardResponse.from_model(dashboard)


@router.put("/dashboards/{dashboard_id}", response_model=SavedDashboardResponse)
def update_dashboard(
    dashboard_id: int,
    payload: SavedDashboardUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    dashboard = get_owned_dashboard(db, dashboard_id, user_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Saved dashboard not found.")

    if payload.name is not None:
        dashboard.name = payload.name
    if payload.widgets is not None:
        dashboard.widgets_json = [w.model_dump() for w in payload.widgets]
    if payload.layout is not None:
        dashboard.layout_json = [l.model_dump() for l in payload.layout]
    if payload.filters is not None:
        dashboard.filters_json = payload.filters.model_dump()

    db.commit()
    db.refresh(dashboard)
    return SavedDashboardResponse.from_model(dashboard)


@router.post("/dashboards/{dashboard_id}/duplicate", response_model=SavedDashboardResponse)
def duplicate_dashboard(
    dashboard_id: int,
    payload: SavedDashboardDuplicate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    original = get_owned_dashboard(db, dashboard_id, user_id)
    if not original:
        raise HTTPException(status_code=404, detail="Saved dashboard not found.")

    copy = SavedDashboard(
        user_id=user_id,
        file_id=original.file_id,
        name=payload.name or f"{original.name} (copy)",
        widgets_json=original.widgets_json,
        layout_json=original.layout_json,
        filters_json=original.filters_json,
    )
    db.add(copy)
    db.commit()
    db.refresh(copy)
    return SavedDashboardResponse.from_model(copy)


@router.delete("/dashboards/{dashboard_id}", status_code=204)
def delete_dashboard(
    dashboard_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    dashboard = get_owned_dashboard(db, dashboard_id, user_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Saved dashboard not found.")

    db.delete(dashboard)
    db.commit()
    return None
