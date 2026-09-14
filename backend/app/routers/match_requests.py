"""Match request / appointment workflow."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import Appointment, MatchRequest, User
from app.schemas import CreateMatchRequestBody, MatchRequestOut, PatchMatchRequestBody
from app.serializers import match_request_out
from app.services.auth import get_current_user, require_role
from app.services.matching import score_pair

router = APIRouter(prefix="/match-requests", tags=["match-requests"])


def _load_users(db: Session, ids: set[int]) -> dict[int, User]:
    if not ids:
        return {}
    rows = db.scalars(select(User).where(User.id.in_(ids))).all()
    return {u.id: u for u in rows}


@router.get("", response_model=list[MatchRequestOut])
def list_requests(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MatchRequestOut]:
    q = select(MatchRequest).options(joinedload(MatchRequest.appointment)).where(
        MatchRequest.org_id == user.org_id
    )
    if user.role == "patient":
        q = q.where(MatchRequest.patient_user_id == user.id)
    elif user.role == "provider":
        q = q.where(MatchRequest.provider_user_id == user.id)
    # admin: all in org
    rows = db.scalars(q.order_by(MatchRequest.created_at.desc())).unique().all()
    users = _load_users(db, {r.patient_user_id for r in rows} | {r.provider_user_id for r in rows})
    return [match_request_out(r, users) for r in rows]


@router.post("", response_model=MatchRequestOut, status_code=status.HTTP_201_CREATED)
def create_request(
    body: CreateMatchRequestBody,
    user: User = Depends(require_role("patient")),
    db: Session = Depends(get_db),
) -> MatchRequestOut:
    patient = db.scalar(
        select(User)
        .options(joinedload(User.patient_profile))
        .where(User.id == user.id)
    )
    provider = db.scalar(
        select(User)
        .options(joinedload(User.provider_profile))
        .where(
            User.id == body.provider_user_id,
            User.org_id == user.org_id,
            User.role == "provider",
        )
    )
    if not patient or not patient.patient_profile:
        raise HTTPException(status_code=400, detail="Patient profile missing")
    if not provider or not provider.provider_profile:
        raise HTTPException(status_code=404, detail="Provider not found in tenant")

    existing = db.scalar(
        select(MatchRequest).where(
            MatchRequest.patient_user_id == patient.id,
            MatchRequest.provider_user_id == provider.id,
            MatchRequest.status.in_(("open", "accepted", "scheduled")),
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="Active request already exists for this provider")

    pp = patient.patient_profile
    rp = provider.provider_profile
    breakdown = score_pair(
        preferred_specialties={s.strip() for s in pp.preferred_specialties.split(",") if s.strip()},
        provider_specialties={s.strip() for s in rp.specialties.split(",") if s.strip()},
        patient_city=pp.city,
        patient_region=pp.region,
        provider_city=rp.city,
        provider_region=rp.region,
        patient_tier=pp.access_tier,
        accepted_tiers={t.strip() for t in rp.accepted_tiers.split(",") if t.strip()},
        remaining_slots=rp.remaining_slots,
        weekly_capacity=rp.weekly_capacity,
    )

    row = MatchRequest(
        org_id=user.org_id,
        patient_user_id=patient.id,
        provider_user_id=provider.id,
        score=breakdown.score,
        status="open",
        notes=body.notes.strip(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    users = _load_users(db, {row.patient_user_id, row.provider_user_id})
    return match_request_out(row, users)


@router.patch("/{request_id}", response_model=MatchRequestOut)
def patch_request(
    request_id: int,
    body: PatchMatchRequestBody,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MatchRequestOut:
    row = db.scalar(
        select(MatchRequest)
        .options(joinedload(MatchRequest.appointment))
        .where(MatchRequest.id == request_id, MatchRequest.org_id == user.org_id)
    )
    if not row:
        raise HTTPException(status_code=404, detail="Match request not found")

    if user.role == "patient" and row.patient_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your request")
    if user.role == "provider" and row.provider_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not your inbox item")
    if user.role == "patient" and body.status not in ("declined",):
        # patients may cancel/decline their own open request
        if body.status != "declined":
            raise HTTPException(status_code=403, detail="Patients may only decline/cancel")

    if body.status == "scheduled":
        when = body.scheduled_for or (datetime.now(timezone.utc) + timedelta(days=7))
        if row.appointment:
            row.appointment.scheduled_for = when
            row.appointment.status = "proposed"
        else:
            db.add(
                Appointment(
                    match_request_id=row.id,
                    scheduled_for=when,
                    status="proposed",
                )
            )
        row.status = "scheduled"
        # consume a slot when scheduling
        provider = db.scalar(
            select(User)
            .options(joinedload(User.provider_profile))
            .where(User.id == row.provider_user_id)
        )
        if provider and provider.provider_profile and provider.provider_profile.remaining_slots > 0:
            provider.provider_profile.remaining_slots -= 1
    else:
        row.status = body.status

    db.commit()
    db.refresh(row)
    # reload appointment
    row = db.scalar(
        select(MatchRequest)
        .options(joinedload(MatchRequest.appointment))
        .where(MatchRequest.id == row.id)
    )
    assert row is not None
    users = _load_users(db, {row.patient_user_id, row.provider_user_id})
    return match_request_out(row, users)
