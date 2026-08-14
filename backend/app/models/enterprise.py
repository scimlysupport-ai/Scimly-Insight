from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean
from app.database.session import Base


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String, nullable=False, default="member")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DashboardShare(Base):
    __tablename__ = "dashboard_shares"

    id = Column(Integer, primary_key=True, index=True)
    dashboard_id = Column(Integer, nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    permission = Column(String, nullable=False, default="view")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class RefreshSchedule(Base):
    __tablename__ = "refresh_schedules"

    id = Column(Integer, primary_key=True, index=True)
    dashboard_id = Column(Integer, nullable=False, index=True)
    cron_expression = Column(String, nullable=False, default="0 * * * *")
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id = Column(Integer, primary_key=True, index=True)
    dashboard_id = Column(Integer, nullable=False, index=True)
    title = Column(String, nullable=False)
    metric = Column(String, nullable=False)
    threshold = Column(String, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class VersionSnapshot(Base):
    __tablename__ = "version_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    dashboard_id = Column(Integer, nullable=False, index=True)
    version_label = Column(String, nullable=False, default="v1")
    snapshot_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
