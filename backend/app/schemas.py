"""Pydantic schemas for MatchCare API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

Tier = Literal["basic", "standard", "premium"]
Role = Literal["patient", "provider", "admin"]
MatchStatus = Literal["open", "accepted", "declined", "scheduled"]
AppointmentStatus = Literal["proposed", "confirmed", "cancelled"]


def _split_csv(value: str) -> list[str]:
    if not value:
        return []
    return [p.strip() for p in value.split(",") if p.strip()]


class TokenRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=4, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OrgOut(BaseModel):
    id: int
    name: str
    slug: str
    subscription_tier: str

    model_config = {"from_attributes": True}


class ProviderOut(BaseModel):
    user_id: int
    display_name: str
    email: str
    specialties: list[str]
    city: str
    region: str
    weekly_capacity: int
    remaining_slots: int
    accepted_tiers: list[str]
    bio: str


class PatientOut(BaseModel):
    user_id: int
    display_name: str
    preferred_specialties: list[str]
    city: str
    region: str
    access_tier: str


class UserMe(BaseModel):
    id: int
    email: str
    display_name: str
    role: Role
    organization: OrgOut
    patient: PatientOut | None = None
    provider: ProviderOut | None = None


class PersonaOut(BaseModel):
    email: str
    password: str
    role: Role
    display_name: str
    org_slug: str
    org_name: str


class ScoreBreakdown(BaseModel):
    specialty: float
    location: float
    tier: float
    availability: float
    weights: dict[str, float]


class MatchResult(BaseModel):
    provider: ProviderOut
    score: float
    breakdown: ScoreBreakdown


class MatchRequestBody(BaseModel):
    preferred_specialties: list[str] | None = None
    city: str | None = Field(default=None, max_length=80)
    region: str | None = Field(default=None, max_length=80)
    require_tier: bool = True
    limit: int = Field(default=10, ge=1, le=50)

    @field_validator("preferred_specialties")
    @classmethod
    def _normalize_specs(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        cleaned = [s.strip() for s in v if s and s.strip()]
        if len(cleaned) > 12:
            raise ValueError("Too many specialties (max 12)")
        return cleaned


class MatchResponse(BaseModel):
    patient: PatientOut
    results: list[MatchResult]
    formula: str


class CreateMatchRequestBody(BaseModel):
    provider_user_id: int
    notes: str = Field(default="", max_length=280)


class PatchMatchRequestBody(BaseModel):
    status: MatchStatus
    scheduled_for: datetime | None = None


class AppointmentOut(BaseModel):
    id: int
    scheduled_for: datetime
    status: AppointmentStatus

    model_config = {"from_attributes": True}


class MatchRequestOut(BaseModel):
    id: int
    org_id: int
    patient_user_id: int
    patient_name: str
    provider_user_id: int
    provider_name: str
    score: float
    status: MatchStatus
    notes: str
    created_at: datetime
    appointment: AppointmentOut | None = None


class TenantSummary(BaseModel):
    organization: OrgOut
    patient_count: int
    provider_count: int
    admin_count: int
    open_requests: int
    accepted_requests: int
    scheduled_requests: int
    specialties_offered: list[str]


class AuditLogOut(BaseModel):
    id: int
    method: str
    path: str
    status_code: int
    actor_user_id: int | None
    org_id: int | None
    duration_ms: int
    created_at: datetime

    model_config = {"from_attributes": True}


class HealthOut(BaseModel):
    status: str
    service: str


class ReadyOut(BaseModel):
    status: str
    organizations: int
    users: int
