"""Liveness and readiness probes."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Organization, User
from app.schemas import HealthOut, ReadyOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    return HealthOut(status="ok", service="matchcare")


@router.get("/ready", response_model=ReadyOut)
def ready(db: Session = Depends(get_db)) -> ReadyOut:
    orgs = db.scalar(select(func.count()).select_from(Organization)) or 0
    users = db.scalar(select(func.count()).select_from(User)) or 0
    status = "ready" if orgs > 0 and users > 0 else "not_ready"
    return ReadyOut(status=status, organizations=orgs, users=users)
