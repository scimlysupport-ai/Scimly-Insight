from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict


class ColumnSchema(BaseModel):
    name: str
    dtype: str
    stats: dict[str, Any]


class ProcessingProgressResponse(BaseModel):
    """Phase 13 — polled by the frontend while a large file is being
    analyzed in the background. `status` mirrors the stages
    progress_service.VALID_STAGES writes ("queued", "reading",
    "cleaning", "analyzing", "saving", "ready", "failed")."""

    status: str
    progress: int
    message: Optional[str] = None


class AIInsight(BaseModel):
    title: str
    text: str


class AIInsightsResponse(BaseModel):
    insights: list[AIInsight]


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: int
    file_id: int
    rows: int
    columns: int
    columns_schema: list[ColumnSchema]
    created_at: datetime

    @classmethod
    def from_dataset(cls, dataset) -> "DatasetResponse":
        """Builds the response explicitly, mapping the DB column
        `schema_json` to the API field `columns_schema`."""
        return cls(
            id=dataset.id,
            file_id=dataset.file_id,
            rows=dataset.rows,
            columns=dataset.columns,
            columns_schema=dataset.schema_json,
            created_at=dataset.created_at,
        )
