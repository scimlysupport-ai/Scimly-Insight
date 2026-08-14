from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database.session import get_db
from app.api.deps import get_current_user
from app.models.enterprise import Team, TeamMember, DashboardShare, RefreshSchedule, AlertRule, AuditEvent, VersionSnapshot
from app.models.saved_dashboard import SavedDashboard
from app.models.user import User
from app.schemas.enterprise.enterprise import (
    TeamCreateRequest,
    TeamResponse,
    TeamMemberRequest,
    ShareRequest,
    ScheduleRequest,
    AlertRequest,
    AuditEventResponse,
    VersionSnapshotResponse,
)

router = APIRouter(prefix="/enterprise", tags=["enterprise"])


def log_audit_event(db: Session, user: User, entity_type: str, entity_id: int, action: str, details: dict | None = None):
    event = AuditEvent(user_id=user.id, entity_type=entity_type, entity_id=entity_id, action=action, details=details or {})
    db.add(event)


def _owned_dashboard(db: Session, dashboard_id: int, user: User) -> SavedDashboard:
    """Every write below (share, schedule, alert, snapshot) operates on
    a specific dashboard_id the caller supplies. Without this check,
    any logged-in user could create a share/schedule/alert/snapshot
    against *any* dashboard just by guessing an id -- ownership was
    never verified. 404 (not 403) on both "doesn't exist" and "not
    yours" so this endpoint can't be used to probe which dashboard ids
    exist."""
    dashboard = db.query(SavedDashboard).filter(SavedDashboard.id == dashboard_id).first()
    if not dashboard or dashboard.user_id != user.id:
        raise HTTPException(status_code=404, detail="Dashboard not found.")
    return dashboard


def _dashboard_with_view_access(db: Session, dashboard_id: int, user: User) -> SavedDashboard:
    """Like _owned_dashboard, but also allows anyone the dashboard has
    actually been shared with (directly, or via a team they belong
    to) -- used for read-only endpoints like version history, where
    "can view the dashboard" is the right bar, not "owns it"."""
    dashboard = db.query(SavedDashboard).filter(SavedDashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found.")
    if dashboard.user_id == user.id:
        return dashboard

    team_ids = [row[0] for row in db.query(TeamMember.team_id).filter(TeamMember.user_id == user.id).all()]
    has_share = (
        db.query(DashboardShare)
        .filter(
            DashboardShare.dashboard_id == dashboard_id,
            or_(DashboardShare.user_id == user.id, DashboardShare.team_id.in_(team_ids) if team_ids else False),
        )
        .first()
    )
    if not has_share:
        raise HTTPException(status_code=404, detail="Dashboard not found.")
    return dashboard


@router.get("/teams", response_model=list[TeamResponse])
def list_teams(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    memberships = db.query(TeamMember.team_id).filter(TeamMember.user_id == user.id).subquery()
    teams = db.query(Team).filter(or_(Team.owner_id == user.id, Team.id.in_(memberships))).all()
    return [
        TeamResponse(id=team.id, name=team.name, description=team.description, owner_id=team.owner_id)
        for team in teams
    ]


@router.get("/users")
def list_users(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Deliberately doesn't return email: this powers a "pick a teammate"
    # dropdown, not a directory. Returning every user's email to any
    # authenticated account is an account-enumeration leak with no
    # feature benefit -- a name is enough to pick the right person from
    # a short list. Capped, too, so this doesn't become an unbounded
    # full-table dump as the user base grows.
    users = db.query(User).filter(User.id != user.id).limit(200).all()
    return [{"id": person.id, "name": person.name or f"User {person.id}"} for person in users]


@router.post("/teams", response_model=TeamResponse)
def create_team(payload: TeamCreateRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    team = Team(name=payload.name, description=payload.description, owner_id=user.id)
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=user.id, role="owner"))
    log_audit_event(db, user, "team", team.id, "created_team", {"name": team.name})
    db.commit()
    db.refresh(team)
    return TeamResponse(id=team.id, name=team.name, description=team.description, owner_id=team.owner_id)


@router.post("/teams/{team_id}/members")
def add_team_member(team_id: int, payload: TeamMemberRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id, Team.owner_id == user.id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    invitee = db.query(User).filter(User.id == payload.user_id).first()
    if not invitee:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == payload.user_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="User is already a member of this team")

    member = TeamMember(team_id=team_id, user_id=payload.user_id, role=payload.role)
    db.add(member)
    log_audit_event(db, user, "team_member", team_id, "added_member", {"user_id": payload.user_id, "role": payload.role})
    db.commit()
    return {"ok": True}


@router.get("/teams/{team_id}/members")
def list_team_members(team_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    is_member = db.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == user.id).first()
    if team.owner_id != user.id and not is_member:
        raise HTTPException(status_code=403, detail="Access denied")

    members = (
        db.query(TeamMember, User)
        .join(User, User.id == TeamMember.user_id)
        .filter(TeamMember.team_id == team_id)
        .all()
    )
    return [
        {
            "id": member.id,
            "user_id": person.id,
            "name": person.name or f"User {person.id}",
            "email": person.email,
            "role": member.role,
            "created_at": member.created_at.isoformat(),
        }
        for member, person in members
    ]


@router.post("/shares")
def create_share(payload: ShareRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _owned_dashboard(db, payload.dashboard_id, user)

    if payload.team_id is not None:
        is_member = (
            db.query(TeamMember)
            .filter(TeamMember.team_id == payload.team_id, TeamMember.user_id == user.id)
            .first()
        )
        if not is_member:
            raise HTTPException(status_code=404, detail="Team not found.")

    share = DashboardShare(
        dashboard_id=payload.dashboard_id,
        team_id=payload.team_id,
        user_id=payload.user_id,
        permission=payload.permission,
    )
    db.add(share)
    log_audit_event(db, user, "dashboard_share", payload.dashboard_id, "created_share", {"permission": payload.permission})
    db.commit()
    return {"ok": True}


@router.post("/schedules")
def create_schedule(payload: ScheduleRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _owned_dashboard(db, payload.dashboard_id, user)
    schedule = RefreshSchedule(**payload.model_dump())
    db.add(schedule)
    log_audit_event(db, user, "refresh_schedule", payload.dashboard_id, "created_schedule", {"cron": payload.cron_expression})
    db.commit()
    return {"ok": True}


@router.post("/alerts")
def create_alert(payload: AlertRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _owned_dashboard(db, payload.dashboard_id, user)
    rule = AlertRule(**payload.model_dump())
    db.add(rule)
    log_audit_event(db, user, "alert_rule", payload.dashboard_id, "created_alert", {"metric": payload.metric, "threshold": payload.threshold})
    db.commit()
    return {"ok": True}


@router.get("/audit-logs", response_model=list[AuditEventResponse])
def list_audit_logs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    own_team_ids = [row[0] for row in db.query(TeamMember.team_id).filter(TeamMember.user_id == user.id).all()]
    events = (
        db.query(AuditEvent)
        .filter(
            or_(
                AuditEvent.user_id == user.id,
                AuditEvent.entity_id.in_(own_team_ids) if own_team_ids else False,
            )
        )
        .order_by(AuditEvent.created_at.desc())
        .all()
    )
    return [
        AuditEventResponse(
            id=event.id,
            user_id=event.user_id,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            action=event.action,
            details=event.details,
            created_at=event.created_at.isoformat(),
        )
        for event in events
    ]


@router.post("/version-history")
def create_version_snapshot(dashboard_id: int, version_label: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _owned_dashboard(db, dashboard_id, user)
    snapshot = VersionSnapshot(dashboard_id=dashboard_id, version_label=version_label, snapshot_json={"user_id": user.id, "saved_at": str(__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat())})
    db.add(snapshot)
    log_audit_event(db, user, "version_snapshot", dashboard_id, "created_version", {"version_label": version_label})
    db.commit()
    return {"ok": True}


@router.get("/version-history/{dashboard_id}", response_model=list[VersionSnapshotResponse])
def get_version_history(dashboard_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _dashboard_with_view_access(db, dashboard_id, user)
    snapshots = db.query(VersionSnapshot).filter(VersionSnapshot.dashboard_id == dashboard_id).order_by(VersionSnapshot.created_at.desc()).all()
    return [
        VersionSnapshotResponse(
            id=snapshot.id,
            dashboard_id=snapshot.dashboard_id,
            version_label=snapshot.version_label,
            snapshot_json=snapshot.snapshot_json,
            created_at=snapshot.created_at.isoformat(),
        )
        for snapshot in snapshots
    ]


@router.get("/shared-dashboards")
def list_shared_dashboards(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    team_ids = [row[0] for row in db.query(TeamMember.team_id).filter(TeamMember.user_id == user.id).all()]
    shared = (
        db.query(DashboardShare, SavedDashboard)
        .join(SavedDashboard, SavedDashboard.id == DashboardShare.dashboard_id)
        .filter(
            or_(
                DashboardShare.user_id == user.id,
                DashboardShare.team_id.in_(team_ids) if team_ids else False,
            )
        )
        .all()
    )
    return [
        {
            "id": dashboard.id,
            "name": dashboard.name,
            "file_id": dashboard.file_id,
            "permission": share.permission,
            "shared_via": "team" if share.team_id else "user",
        }
        for share, dashboard in shared
    ]
