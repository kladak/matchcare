"""ORM → schema helpers."""

from __future__ import annotations

from app.models import MatchRequest, PatientProfile, ProviderProfile, User
from app.schemas import AppointmentOut, MatchRequestOut, OrgOut, PatientOut, ProviderOut, UserMe, _split_csv


def provider_out(user: User, profile: ProviderProfile) -> ProviderOut:
    return ProviderOut(
        user_id=user.id,
        display_name=user.display_name,
        email=user.email,
        specialties=_split_csv(profile.specialties),
        city=profile.city,
        region=profile.region,
        weekly_capacity=profile.weekly_capacity,
        remaining_slots=profile.remaining_slots,
        accepted_tiers=_split_csv(profile.accepted_tiers),
        bio=profile.bio,
    )


def patient_out(user: User, profile: PatientProfile) -> PatientOut:
    return PatientOut(
        user_id=user.id,
        display_name=user.display_name,
        preferred_specialties=_split_csv(profile.preferred_specialties),
        city=profile.city,
        region=profile.region,
        access_tier=profile.access_tier,
    )


def user_me(user: User) -> UserMe:
    return UserMe(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,  # type: ignore[arg-type]
        organization=OrgOut.model_validate(user.organization),
        patient=patient_out(user, user.patient_profile) if user.patient_profile else None,
        provider=provider_out(user, user.provider_profile) if user.provider_profile else None,
    )


def match_request_out(row: MatchRequest, db_users: dict[int, User]) -> MatchRequestOut:
    patient = db_users.get(row.patient_user_id)
    provider = db_users.get(row.provider_user_id)
    appt = None
    if row.appointment:
        appt = AppointmentOut.model_validate(row.appointment)
    return MatchRequestOut(
        id=row.id,
        org_id=row.org_id,
        patient_user_id=row.patient_user_id,
        patient_name=patient.display_name if patient else f"user:{row.patient_user_id}",
        provider_user_id=row.provider_user_id,
        provider_name=provider.display_name if provider else f"user:{row.provider_user_id}",
        score=row.score,
        status=row.status,  # type: ignore[arg-type]
        notes=row.notes,
        created_at=row.created_at,
        appointment=appt,
    )
