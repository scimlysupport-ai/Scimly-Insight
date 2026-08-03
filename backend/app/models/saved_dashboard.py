"""
Phase 10 — Save Dashboard.

A SavedDashboard is a named snapshot of a dashboard: which widgets it
has (chart type, column choices, colors, titles — i.e. every Phase 7
edit baked in), where they sit on the grid (Phase 8's layout), and
which global filters (Phase 9) were active. Widgets/layout/filters are
stored as JSON rather than as separate normalized tables — a dashboard
is always read and written as one whole document (open it, edit it,
save it back), never queried widget-by-widget, so JSON columns keep
save/open/duplicate simple with no join fan-out.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from app.database.session import Base


class SavedDashboard(Base):
    __tablename__ = "saved_dashboards"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    file_id = Column(Integer, ForeignKey("uploaded_files.id"), nullable=False, index=True)

    name = Column(String, nullable=False, default="Untitled dashboard")

    widgets_json = Column(JSON, nullable=False, default=list)  # list[SavedWidget]
    layout_json = Column(JSON, nullable=False, default=list)  # list[LayoutItem]
    filters_json = Column(JSON, nullable=False, default=dict)  # DashboardFilters

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
