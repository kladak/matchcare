# MatchCare — Product Spec

**Karim Ladak · portfolio / educational demo**  
**Status:** runnable local demo (pending cloud deployment)

## One-liner

Multi-tenant specialty matching SaaS — patients discover ranked providers by specialty preference, location, subscription tier, and capacity; clinicians and tenant admins manage their side of the funnel.

## Honesty / scope

- Educational portfolio demo only. **Synthetic** seed data.
- **Independent clean-room build.** Not affiliated with SpeciaList Health, Precision Cardiology, Syncura, or any prior employer/collaborator codebases.
- **No HIPAA certification claims.** No fake MAU, “10k users,” clinical outcomes, or production healthcare deployments.
- Demo JWT auth (one-click personas). Audit logs store request metadata / hashed ids only — never clinical notes or real PHI.
- Metrics and rankings are computed from the seeded generator (fixed RNG) — reproducible for screenshots and demos.

## Problem

Specialty referral and access routing is noisy: patients need providers who match clinical interest *and* are reachable under their plan tier, near them, and not overbooked. Raw directories hide capacity and tier constraints.

## Solution (demo)

1. **Multi-tenant orgs** — isolated tenants with their own providers, patients, and subscription tier.
2. **Role-aware JWT auth** — `patient` · `provider` · `admin` demo personas.
3. **Explainable matching** — ranked scores with a documented breakdown (specialty, location, tier, availability).
4. **Match requests / appointments** — patients open a request; providers/admins see inbound queue.
5. **Dashboard** — login → browse → match → score cards; provider inbox; admin tenant overview.

## Matching score formula

For patient *P* and provider *R*, overall score ∈ [0, 1]:

```
score = 0.40·S_specialty + 0.25·S_location + 0.20·S_tier + 0.15·S_availability
```

| Component | Formula | Meaning |
|-----------|---------|---------|
| **S_specialty** | Jaccard(`P.preferred_specialties`, `R.specialties`) | Overlap of clinical interests |
| **S_location** | `1.0` same city · `0.55` same region · `0.15` otherwise | Geographic fit |
| **S_tier** | `1.0` if `P.access_tier` ∈ `R.accepted_tiers` else `0.0` (hard gate softens to 0 — filtered out when `require_tier=true`) | Plan / subscription access |
| **S_availability** | `remaining_weekly_slots / weekly_capacity` clipped to [0, 1] | Capacity headroom |

**Interpretation for recruiters:** weights emphasize specialty fit first; tier is a gate (demo defaults to filtering zero-tier matches); availability prevents always ranking fully booked clinicians first. Breakdown is returned with every ranked row so the UI can explain *why*.

Weights and soft/hard tier behavior are constants in `app/services/matching.py` — easy to tune for demos.

## Data model (synthetic)

- **Organization:** id, name, slug, subscription_tier (`basic` \| `standard` \| `premium`)
- **User:** id, org_id, email, role, display_name, password_hash
- **ProviderProfile:** user_id, specialties[], city, region, weekly_capacity, remaining_slots, accepted_tiers[]
- **PatientProfile:** user_id, preferred_specialties[], city, region, access_tier
- **MatchRequest:** patient_id, provider_id, score, status (`open` \| `accepted` \| `declined` \| `scheduled`), created_at
- **Appointment:** match_request_id, scheduled_for, status (`proposed` \| `confirmed` \| `cancelled`)
- **RequestLog:** id, method, path, status_code, actor_user_id (nullable), org_id (nullable), duration_ms, created_at — no bodies/PII

Seed is deterministic (fixed RNG seed) so demo script and screenshots stay stable.

## API surface

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | Liveness |
| GET | `/ready` | Readiness (DB + seed loaded) |
| POST | `/auth/token` | Email/password → JWT |
| GET | `/auth/me` | Current user + role + org |
| GET | `/auth/personas` | Demo login personas (no secrets in prod sense — demo only) |
| GET | `/providers` | Browse providers in tenant (filters: specialty, city) |
| POST | `/match` | Ranked matches for current patient (+ score breakdown) |
| POST | `/match-requests` | Create match request from a ranked provider |
| GET | `/match-requests` | Role-scoped inbox (patient own / provider inbound / admin all) |
| PATCH | `/match-requests/{id}` | Accept / decline / schedule |
| GET | `/admin/tenant` | Admin: org summary, counts, recent requests |
| GET | `/audit/logs` | Admin: recent request logs (ids/metadata only) |

Typed Pydantic response models throughout. Input validated on create/patch bodies.

## Non-goals

- Real EHR / claims / payer integrations
- HIPAA certification or BAAs
- Production identity providers, MFA, or SSO
- Claiming live patient volume or clinical efficacy

## Architecture

```
Vite/React (dashboard)
        │  Bearer JWT
        ▼
FastAPI  ── SQLAlchemy / SQLite ── seed on startup
        │
   matching service · auth · audit middleware
```

Optional: `docker compose up` runs API + static frontend.

## Demo personas

| Role | Email | Password |
|------|-------|----------|
| Patient | `patient@demo.matchcare.local` | `demo1234` |
| Provider | `provider@demo.matchcare.local` | `demo1234` |
| Admin | `admin@demo.matchcare.local` | `demo1234` |

Second tenant (`summit`) has its own admin/patient for multi-tenant isolation demos.
