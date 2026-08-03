"""
Request/response shapes for Phase 10 — Save Dashboard.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.schemas.filters import DashboardFilters


class SavedWidget(BaseModel):
    """One widget's full, self-contained definition — every Phase 7 edit
    (chart type, column/axis choices, color, title) already baked in.
    No separate "override" concept here; a saved widget just *is* its
    current state."""
    chart: str  # "kpi" | "line" | "pie" | "bar" | "table"
    title: str
    column: Optional[str] = None
    x: Optional[str] = None
    y: Optional[str] = None
    columns: Optional[list[str]] = None
    color: Optional[str] = None


class LayoutItem(BaseModel):
    i: str
    x: int
    y: int
    w: int
    h: int


class SavedDashboardCreate(BaseModel):
    file_id: int
    name: str = "Untitled dashboard"
    widgets: list[SavedWidget] = Field(default_factory=list)
    layout: list[LayoutItem] = Field(default_factory=list)
    filters: DashboardFilters = Field(default_factory=DashboardFilters)


class SavedDashboardUpdate(BaseModel):
    """All fields optional so a rename doesn't require resending widgets."""
    name: Optional[str] = None
    widgets: Optional[list[SavedWidget]] = None
    layout: Optional[list[LayoutItem]] = None
    filters: Optional[DashboardFilters] = None


class SavedDashboardDuplicate(BaseModel):
    name: Optional[str] = None  # defaults to "<original name> (copy)"


class SavedDashboardResponse(BaseModel):
    id: int
    file_id: int
    name: str
    widgets: list[SavedWidget]
    layout: list[LayoutItem]
    filters: DashboardFilters
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, dashboard) -> "SavedDashboardResponse":
        return cls(
            id=dashboard.id,
            file_id=dashboard.file_id,
            name=dashboard.name,
            widgets=dashboard.widgets_json or [],
            layout=dashboard.layout_json or [],
            filters=dashboard.filters_json or DashboardFilters(),
            created_at=dashboard.created_at,
            updated_at=dashboard.updated_at,
        )


class SavedDashboardSummary(BaseModel):
    """Lighter shape for list views — no widgets/layout payload."""
    id: int
    file_id: int
    file_name: Optional[str] = None
    name: str
    widget_count: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, dashboard, file_name: Optional[str] = None) -> "SavedDashboardSummary":
        return cls(
            id=dashboard.id,
            file_id=dashboard.file_id,
            file_name=file_name,
            name=dashboard.name,
            widget_count=len(dashboard.widgets_json or []),
            created_at=dashboard.created_at,
            updated_at=dashboard.updated_at,
        )


class WidgetsDataRequest(BaseModel):
    """Given a list of widget definitions (e.g. from a saved dashboard),
    compute the actual chart data for each — the same computation the
    auto-generated dashboard uses, just for an arbitrary widget list
    instead of the recommendation engine's output."""
    widgets: list[SavedWidget]
    filters: DashboardFilters = Field(default_factory=DashboardFilters)
