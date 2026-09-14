"""Demo JWT auth and personas."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models import User
from app.schemas import PersonaOut, TokenRequest, TokenResponse, UserMe
from app.seed import list_personas
from app.serializers import user_me
from app.services.auth import create_access_token, get_current_user, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenResponse)
def login(body: TokenRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(
        select(User)
        .options(
            joinedload(User.organization),
            joinedload(User.patient_profile),
            joinedload(User.provider_profile),
        )
        .where(User.email == body.email.lower())
    )
    # Demo: email is unique across seed; if duplicates across tenants, first match wins.
    if user is None:
        # try case-sensitive fallback across all
        user = db.scalar(
            select(User)
            .options(
                joinedload(User.organization),
                joinedload(User.patient_profile),
                joinedload(User.provider_profile),
            )
            .where(User.email == body.email)
        )
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(user))


@router.get("/me", response_model=UserMe)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> UserMe:
    fresh = db.scalar(
        select(User)
        .options(
            joinedload(User.organization),
            joinedload(User.patient_profile),
            joinedload(User.provider_profile),
        )
        .where(User.id == user.id)
    )
    assert fresh is not None
    return user_me(fresh)


@router.get("/personas", response_model=list[PersonaOut])
def personas() -> list[PersonaOut]:
    return [PersonaOut(**p) for p in list_personas()]
