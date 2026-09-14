"""Ranked specialty matching for patients."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import User
from app.schemas import MatchRequestBody, MatchResponse, MatchResult, ScoreBreakdown
from app.serializers import patient_out, provider_out
from app.services.auth import require_role
from app.services.matching import FORMULA, WEIGHTS, score_pair

router = APIRouter(tags=["match"])


@router.post("/match", response_model=MatchResponse)
def run_match(
    body: MatchRequestBody,
    user: User = Depends(require_role("patient")),
    db: Session = Depends(get_db),
) -> MatchResponse:
    fresh = db.scalar(
        select(User)
        .options(joinedload(User.patient_profile), joinedload(User.organization))
        .where(User.id == user.id)
    )
    assert fresh is not None
    if not fresh.patient_profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Patient profile missing")

    profile = fresh.patient_profile
    preferred = body.preferred_specialties or [
        s.strip() for s in profile.preferred_specialties.split(",") if s.strip()
    ]
    city = (body.city or profile.city).strip()
    region = (body.region or profile.region).strip()

    providers = db.scalars(
        select(User)
        .options(joinedload(User.provider_profile))
        .where(User.org_id == fresh.org_id, User.role == "provider")
    ).unique().all()

    results: list[MatchResult] = []
    for pu in providers:
        pp = pu.provider_profile
        if not pp:
            continue
        breakdown = score_pair(
            preferred_specialties=set(preferred),
            provider_specialties={s.strip() for s in pp.specialties.split(",") if s.strip()},
            patient_city=city,
            patient_region=region,
            provider_city=pp.city,
            provider_region=pp.region,
            patient_tier=profile.access_tier,
            accepted_tiers={t.strip() for t in pp.accepted_tiers.split(",") if t.strip()},
            remaining_slots=pp.remaining_slots,
            weekly_capacity=pp.weekly_capacity,
        )
        if body.require_tier and breakdown.tier <= 0:
            continue
        results.append(
            MatchResult(
                provider=provider_out(pu, pp),
                score=breakdown.score,
                breakdown=ScoreBreakdown(
                    **breakdown.as_dict(),
                    weights=dict(WEIGHTS),
                ),
            )
        )

    results.sort(key=lambda r: (-r.score, r.provider.display_name))
    results = results[: body.limit]

    # ephemeral patient view reflecting request overrides
    patient_view = patient_out(fresh, profile).model_copy(
        update={
            "preferred_specialties": preferred,
            "city": city,
            "region": region,
        }
    )
    return MatchResponse(patient=patient_view, results=results, formula=FORMULA)
