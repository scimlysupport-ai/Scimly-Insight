from pydantic import BaseModel, Field
from typing import Optional, List


class TeamCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None


class TeamResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    owner_id: int


class TeamMemberRequest(BaseModel):
    user_id: int
    role: str = "member"


class ShareRequest(BaseModel):
    dashboard_id: int
    team_id: Optional[int] = None
    user_id: Optional[int] = None
    permission: str = "view"


class ScheduleRequest(BaseModel):
    dashboard_id: int
    cron_expression: str = "0 * * * *"
    enabled: bool = True


class AlertRequest(BaseModel):
    dashboard_id: int
    title: str
    metric: str
    threshold: str
    enabled: bool = True


class AuditEventResponse(BaseModel):
    id: int
    user_id: int
    entity_type: str
    entity_id: int
    action: str
    details: Optional[dict] = None
    created_at: str


class VersionSnapshotResponse(BaseModel):
    id: int
    dashboard_id: int
    version_label: str
    snapshot_json: dict
    created_at: str
