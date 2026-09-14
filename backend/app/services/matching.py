"""Explainable specialty matching scores.

score = 0.40·S_specialty + 0.25·S_location + 0.20·S_tier + 0.15·S_availability
"""

from __future__ import annotations

from dataclasses import dataclass

WEIGHTS = {
    "specialty": 0.40,
    "location": 0.25,
    "tier": 0.20,
    "availability": 0.15,
}

FORMULA = (
    "score = 0.40·specialty(Jaccard) + 0.25·location + 0.20·tier + 0.15·availability"
)


@dataclass(frozen=True)
class Breakdown:
    specialty: float
    location: float
    tier: float
    availability: float

    @property
    def score(self) -> float:
        return round(
            WEIGHTS["specialty"] * self.specialty
            + WEIGHTS["location"] * self.location
            + WEIGHTS["tier"] * self.tier
            + WEIGHTS["availability"] * self.availability,
            4,
        )

    def as_dict(self) -> dict[str, float]:
        return {
            "specialty": round(self.specialty, 4),
            "location": round(self.location, 4),
            "tier": round(self.tier, 4),
            "availability": round(self.availability, 4),
        }


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def location_score(patient_city: str, patient_region: str, provider_city: str, provider_region: str) -> float:
    pc = patient_city.strip().lower()
    pr = patient_region.strip().lower()
    rc = provider_city.strip().lower()
    rr = provider_region.strip().lower()
    if pc and pc == rc:
        return 1.0
    if pr and pr == rr:
        return 0.55
    return 0.15


def tier_score(patient_tier: str, accepted_tiers: set[str]) -> float:
    return 1.0 if patient_tier.strip().lower() in {t.lower() for t in accepted_tiers} else 0.0


def availability_score(remaining: int, capacity: int) -> float:
    if capacity <= 0:
        return 0.0
    return max(0.0, min(1.0, remaining / capacity))


def score_pair(
    *,
    preferred_specialties: set[str],
    provider_specialties: set[str],
    patient_city: str,
    patient_region: str,
    provider_city: str,
    provider_region: str,
    patient_tier: str,
    accepted_tiers: set[str],
    remaining_slots: int,
    weekly_capacity: int,
) -> Breakdown:
    return Breakdown(
        specialty=jaccard(
            {s.strip().lower() for s in preferred_specialties if s.strip()},
            {s.strip().lower() for s in provider_specialties if s.strip()},
        ),
        location=location_score(patient_city, patient_region, provider_city, provider_region),
        tier=tier_score(patient_tier, accepted_tiers),
        availability=availability_score(remaining_slots, weekly_capacity),
    )
