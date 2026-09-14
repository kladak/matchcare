"""Deterministic synthetic seed for MatchCare demo."""

from __future__ import annotations

import random

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Organization, PatientProfile, ProviderProfile, User
DEMO_PASSWORD = "demo1234"
# Precomputed bcrypt (rounds=4) for demo1234 — keeps seed/tests fast.
_DEMO_HASH = "$2b$04$IhgBqn3kdVyhZW7gvRSNE.EohRIHjeUvePzBB6B05lgOlBhN.NqsW"
SPECIALTIES = [
    "Cardiology",
    "Dermatology",
    "Endocrinology",
    "Gastroenterology",
    "Neurology",
    "Orthopedics",
    "Psychiatry",
    "Pulmonology",
    "Rheumatology",
    "Oncology",
]


def _csv(items: list[str]) -> str:
    return ",".join(items)


def seed_if_empty(db: Session) -> None:
    count = db.scalar(select(func.count()).select_from(Organization)) or 0
    if count > 0:
        return

    rng = random.Random(42)
    pwd = _DEMO_HASH

    bayview = Organization(name="Bayview Health Network", slug="bayview", subscription_tier="premium")
    summit = Organization(name="Summit Specialty Group", slug="summit", subscription_tier="standard")
    db.add_all([bayview, summit])
    db.flush()

    # --- Bayview personas (primary demo path) ---
    patient = User(
        org_id=bayview.id,
        email="patient@demo.matchcare.local",
        display_name="Ava Chen",
        role="patient",
        password_hash=pwd,
    )
    provider = User(
        org_id=bayview.id,
        email="provider@demo.matchcare.local",
        display_name="Dr. Sam Okonkwo",
        role="provider",
        password_hash=pwd,
    )
    admin = User(
        org_id=bayview.id,
        email="admin@demo.matchcare.local",
        display_name="Morgan Park",
        role="admin",
        password_hash=pwd,
    )
    db.add_all([patient, provider, admin])
    db.flush()

    db.add(
        PatientProfile(
            user_id=patient.id,
            preferred_specialties=_csv(["Cardiology", "Endocrinology"]),
            city="San Francisco",
            region="Bay Area",
            access_tier="premium",
        )
    )
    db.add(
        ProviderProfile(
            user_id=provider.id,
            specialties=_csv(["Cardiology", "Internal Medicine"]),
            city="San Francisco",
            region="Bay Area",
            weekly_capacity=12,
            remaining_slots=7,
            accepted_tiers=_csv(["standard", "premium"]),
            bio="Synthetic cardiology clinic profile for demo matching.",
        )
    )

    # Extra Bayview patients / providers for richer match tables
    extra_providers = [
        ("Dr. Priya Nair", ["Endocrinology", "Internal Medicine"], "Oakland", "Bay Area", 10, 3, ["basic", "standard", "premium"]),
        ("Dr. Luis Ortega", ["Dermatology"], "San Jose", "Bay Area", 8, 8, ["basic", "standard", "premium"]),
        ("Dr. Helen Cho", ["Neurology", "Psychiatry"], "San Francisco", "Bay Area", 6, 1, ["premium"]),
        ("Dr. Marcus Webb", ["Orthopedics", "Rheumatology"], "Berkeley", "Bay Area", 14, 9, ["standard", "premium"]),
        ("Dr. Aisha Rahman", ["Gastroenterology"], "Palo Alto", "Bay Area", 9, 4, ["basic", "standard", "premium"]),
        ("Dr. Noah Feldman", ["Cardiology", "Pulmonology"], "San Francisco", "Bay Area", 11, 0, ["premium"]),
        ("Dr. Yuki Tanaka", ["Oncology", "Internal Medicine"], "Fremont", "Bay Area", 7, 5, ["standard", "premium"]),
    ]
    for i, (name, specs, city, region, cap, rem, tiers) in enumerate(extra_providers):
        u = User(
            org_id=bayview.id,
            email=f"provider{i + 2}@bayview.matchcare.local",
            display_name=name,
            role="provider",
            password_hash=pwd,
        )
        db.add(u)
        db.flush()
        db.add(
            ProviderProfile(
                user_id=u.id,
                specialties=_csv(specs),
                city=city,
                region=region,
                weekly_capacity=cap,
                remaining_slots=rem,
                accepted_tiers=_csv(tiers),
                bio=f"Synthetic {specs[0].lower()} specialist — educational seed only.",
            )
        )

    for i, (name, prefs, city, tier) in enumerate(
        [
            ("Jordan Lee", ["Dermatology"], "San Jose", "standard"),
            ("Riley Kim", ["Neurology", "Psychiatry"], "San Francisco", "premium"),
            ("Casey Brooks", ["Orthopedics"], "Oakland", "basic"),
        ]
    ):
        u = User(
            org_id=bayview.id,
            email=f"patient{i + 2}@bayview.matchcare.local",
            display_name=name,
            role="patient",
            password_hash=pwd,
        )
        db.add(u)
        db.flush()
        db.add(
            PatientProfile(
                user_id=u.id,
                preferred_specialties=_csv(prefs),
                city=city,
                region="Bay Area",
                access_tier=tier,
            )
        )

    # --- Summit tenant (isolation demo) ---
    summit_patient = User(
        org_id=summit.id,
        email="patient@summit.matchcare.local",
        display_name="Taylor Nguyen",
        role="patient",
        password_hash=pwd,
    )
    summit_provider = User(
        org_id=summit.id,
        email="provider@summit.matchcare.local",
        display_name="Dr. Elena Voss",
        role="provider",
        password_hash=pwd,
    )
    summit_admin = User(
        org_id=summit.id,
        email="admin@summit.matchcare.local",
        display_name="Chris Delgado",
        role="admin",
        password_hash=pwd,
    )
    db.add_all([summit_patient, summit_provider, summit_admin])
    db.flush()
    db.add(
        PatientProfile(
            user_id=summit_patient.id,
            preferred_specialties=_csv(["Orthopedics", "Rheumatology"]),
            city="Denver",
            region="Front Range",
            access_tier="standard",
        )
    )
    db.add(
        ProviderProfile(
            user_id=summit_provider.id,
            specialties=_csv(["Orthopedics", "Sports Medicine"]),
            city="Denver",
            region="Front Range",
            weekly_capacity=10,
            remaining_slots=6,
            accepted_tiers=_csv(["basic", "standard", "premium"]),
            bio="Summit tenant synthetic ortho profile.",
        )
    )
    for i in range(3):
        specs = rng.sample(SPECIALTIES, k=2)
        u = User(
            org_id=summit.id,
            email=f"provider{i + 2}@summit.matchcare.local",
            display_name=f"Dr. Summit {i + 2}",
            role="provider",
            password_hash=pwd,
        )
        db.add(u)
        db.flush()
        db.add(
            ProviderProfile(
                user_id=u.id,
                specialties=_csv(specs),
                city=rng.choice(["Denver", "Boulder", "Aurora"]),
                region="Front Range",
                weekly_capacity=rng.randint(6, 14),
                remaining_slots=rng.randint(0, 10),
                accepted_tiers=_csv(["basic", "standard", "premium"]),
                bio="Synthetic Summit provider.",
            )
        )

    db.commit()


def list_personas() -> list[dict]:
    return [
        {
            "email": "patient@demo.matchcare.local",
            "password": DEMO_PASSWORD,
            "role": "patient",
            "display_name": "Ava Chen",
            "org_slug": "bayview",
            "org_name": "Bayview Health Network",
        },
        {
            "email": "provider@demo.matchcare.local",
            "password": DEMO_PASSWORD,
            "role": "provider",
            "display_name": "Dr. Sam Okonkwo",
            "org_slug": "bayview",
            "org_name": "Bayview Health Network",
        },
        {
            "email": "admin@demo.matchcare.local",
            "password": DEMO_PASSWORD,
            "role": "admin",
            "display_name": "Morgan Park",
            "org_slug": "bayview",
            "org_name": "Bayview Health Network",
        },
        {
            "email": "patient@summit.matchcare.local",
            "password": DEMO_PASSWORD,
            "role": "patient",
            "display_name": "Taylor Nguyen",
            "org_slug": "summit",
            "org_name": "Summit Specialty Group",
        },
        {
            "email": "provider@summit.matchcare.local",
            "password": DEMO_PASSWORD,
            "role": "provider",
            "display_name": "Dr. Elena Voss",
            "org_slug": "summit",
            "org_name": "Summit Specialty Group",
        },
        {
            "email": "admin@summit.matchcare.local",
            "password": DEMO_PASSWORD,
            "role": "admin",
            "display_name": "Chris Delgado",
            "org_slug": "summit",
            "org_name": "Summit Specialty Group",
        },
    ]
