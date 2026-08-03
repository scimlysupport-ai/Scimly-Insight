from typing import Optional, Any
from pydantic import BaseModel

from app.schemas.filters import DashboardFilters


class ChartPreviewRequest(BaseModel):
    chart: str  # "kpi" | "line" | "pie" | "bar" | "table"
    column: Optional[str] = None        # used by kpi, pie, bar
    x: Optional[str] = None             # used by line
    y: Optional[str] = None             # used by line
    columns: Optional[list[str]] = None  # used by table
    filters: Optional[DashboardFilters] = None  # active global filters (Phase 9)


class ChartPreviewResponse(BaseModel):
    chart: str
    data: Any