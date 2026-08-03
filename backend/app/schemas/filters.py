"""
Request/response shapes for Phase 9 — Global Filters.
"""
from typing import Optional
from pydantic import BaseModel, Field


class DateRangeFilter(BaseModel):
    start: Optional[str] = None  # ISO date, e.g. "2025-01-01"
    end: Optional[str] = None


class DashboardFilters(BaseModel):
    """
    The filters currently applied to a dashboard. `categorical` maps a
    column name to the list of values still allowed (an empty/missing
    list means "no filter on this column"). For a delimiter-separated
    "tag" column (e.g. "Stale Admin; Admin No Mfa"), the values are
    individual tags, not whole compound strings — see filter_service.
    `date_ranges` maps a column name to a start/end bound.

    Schema-driven rather than hardcoded field names — the original
    roadmap named Date/Country/Product/Department specifically, but a
    real dataset may have none of those. The frontend discovers which
    columns are filterable via GET /dataset/{file_id}/filters.
    """
    categorical: dict[str, list[str]] = Field(default_factory=dict)
    date_ranges: dict[str, DateRangeFilter] = Field(default_factory=dict)


class CategoricalFilterOption(BaseModel):
    column: str
    options: list[str]
    type: str = "categorical"  # "categorical" | "tags"


class DateRangeFilterOption(BaseModel):
    column: str
    min: str
    max: str


class FilterOptionsResponse(BaseModel):
    categorical: list[CategoricalFilterOption]
    date_ranges: list[DateRangeFilterOption]
