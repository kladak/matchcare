"""Tenant admin overview and audit logs."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import MatchRequest, Organization, ProviderProfile, RequestLog, User
from app.schemas import AuditLogOut, OrgOut, TenantSummary, _split_csv
from app.services.auth import require_role

router = APIRouter(tags=["admin"])


@router.get("/admin/tenant", response_model=TenantSummary)
def tenant_summary(
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> TenantSummary:
    org = db.get(Organization, user.org_id)
    assert org is not None

    def count_role(role: str) -> int:
        return db.scalar(
            select(func.count()).select_from(User).where(User.org_id == user.org_id, User.role == role)
        ) or 0

    def count_status(st: str) -> int:
        return db.scalar(
            select(func.count())
            .select_from(MatchRequest)
            .where(MatchRequest.org_id == user.org_id, MatchRequest.status == st)
        ) or 0

    providers = db.scalars(
        select(User)
        .options(joinedload(User.provider_profile))
        .where(User.org_id == user.org_id, User.role == "provider")
    ).unique().all()
    specs: set[str] = set()
    for p in providers:
        if p.provider_profile:
            specs.update(_split_csv(p.provider_profile.specialties))

    return TenantSummary(
        organization=OrgOut.model_validate(org),
        patient_count=count_role("patient"),
        provider_count=count_role("provider"),
        admin_count=count_role("admin"),
        open_requests=count_status("open"),
        accepted_requests=count_status("accepted"),
        scheduled_requests=count_status("scheduled"),
        specialties_offered=sorted(specs),
    )


@router.get("/audit/logs", response_model=list[AuditLogOut])
def audit_logs(
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
) -> list[AuditLogOut]:
    rows = db.scalars(
        select(RequestLog)
        .where(RequestLog.org_id == user.org_id)
        .order_by(RequestLog.id.desc())
        .limit(limit)
    ).all()
    return [AuditLogOut.model_validate(r) for r in rows]
