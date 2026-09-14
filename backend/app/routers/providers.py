"""Browse providers within the caller's tenant."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import ProviderProfile, User
from app.schemas import ProviderOut
from app.serializers import provider_out
from app.services.auth import get_current_user

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=list[ProviderOut])
def list_providers(
    specialty: str | None = Query(default=None),
    city: str | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ProviderOut]:
    rows = db.scalars(
        select(User)
        .options(joinedload(User.provider_profile))
        .where(User.org_id == user.org_id, User.role == "provider")
        .order_by(User.display_name)
    ).unique().all()

    out: list[ProviderOut] = []
    for u in rows:
        if not u.provider_profile:
            continue
        po = provider_out(u, u.provider_profile)
        if specialty and specialty.lower() not in {s.lower() for s in po.specialties}:
            continue
        if city and city.lower() != po.city.lower():
            continue
        out.append(po)
    return out
