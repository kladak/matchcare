# MatchCare

Multi-tenant specialty matching: patients get ranked providers by specialty preference, location, subscription tier and capacity, each with a score breakdown. Providers and tenant admins see the other side of the funnel.

Auth uses bcrypt password hashing, JWTs and role dependencies, seeded with one-click demo
personas. Providers, patients and requests come from `backend/app/seed.py`. Formula and
architecture: [`SPEC.md`](SPEC.md).

---

## Running the demo

From a cold clone:

### 0. Prerequisites (once)

```bash
git clone https://github.com/kladak/matchcare.git
cd matchcare

# Terminal A: API
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal B: dashboard
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**.

### 1. Patient match (~40s)

1. On **Demo login**, click **Continue as Patient** (Ava Chen).
2. Land on **Find matches**, with preferred specialties and city pre-filled from the seed.
3. Click **Run match** for the ranked list with an overall score and breakdown chips (specialty, location, tier, availability).
4. Expand one row to see the formula weights (40% specialty, 25% location, 20% tier, 15% availability).
5. Click **Request match** on the top result; it appears under **My requests**.

### 2. Provider inbox (~20s)

1. **Sign out** → **Continue as Provider** (Dr. Sam Okonkwo).
2. Open **Inbox** for inbound match requests against your profile.
3. **Accept** one → status updates; optional **Propose appointment**.

### 3. Admin tenant (~20s)

1. **Sign out** → **Continue as Admin** (Morgan Park).
2. **Tenant overview**: org name, subscription tier, and counts of patients, providers and open requests.
3. Glance at **Audit log**: method, path, status and actor id per request.
4. Optional: log in as a `summit` persona from `/auth/personas` to see the second tenant.

### 4. Close (~10s)

1. Hit **http://localhost:8000/docs** for the typed OpenAPI surface.
2. `curl localhost:8000/health` and `/ready`.

---

## Architecture

| Layer | Stack |
|-------|--------|
| API | FastAPI, SQLAlchemy, SQLite, JWT (demo), seed on startup |
| Matching | Weighted specialty, location, tier and availability (see SPEC) |
| UI | Vite + React + TypeScript |
| Roles | `patient`, `provider`, `admin` (org-scoped) |
| CI | GitHub Actions (pytest + frontend build/test) |
| Optional | `docker compose up` |

```
frontend (Vite)  →  FastAPI + JWT  →  SQLite seed store
                         └── matching service + audit middleware
```

### Tenant isolation

Every read and write is scoped to the caller's `org_id`, taken from the JWT and re-checked
against the database on each request (`app/services/auth.py`). The scoping is applied in the queries themselves; see the
`User.org_id == user.org_id` / `MatchRequest.org_id == user.org_id` predicates in
`app/routers/providers.py`, `match.py`, `match_requests.py` and `admin.py`. An admin of
one tenant cannot read or mutate another tenant's rows even by guessing ids. Passwords are
bcrypt-hashed; role gating is a FastAPI dependency (`require_role`), covered by
`tests/test_requests_admin.py::test_admin_forbidden_for_patient`. A cross-tenant test for
`match_request` ids is still to be written.

Audit middleware (`app/middleware/audit.py`) records method, path, status and actor id per
request. Bodies are excluded from the row.

## API endpoints

| Path | Description |
|------|-------------|
| `GET /health` | Liveness |
| `GET /ready` | DB + seed ready |
| `POST /auth/token` | Demo login → JWT |
| `GET /auth/me` | Current user |
| `GET /auth/personas` | One-click demo personas |
| `GET /providers` | Browse tenant providers |
| `POST /match` | Ranked matches + score breakdown |
| `POST /match-requests` | Create request |
| `GET /match-requests` | Role-scoped list |
| `PATCH /match-requests/{id}` | Accept / decline / schedule |
| `GET /admin/tenant` | Admin org summary |
| `GET /audit/logs` | Admin request logs |

## How to run

### Local (recommended for demo)

See **Running the demo** above.

Demo password: `demo1234`  
Emails: `patient@demo.matchcare.local`, `provider@demo.matchcare.local`, `admin@demo.matchcare.local`

### Tests

```bash
cd backend && source .venv/bin/activate && pytest -q
cd frontend && npm test && npm run build
```

### Docker (optional)

```bash
docker compose up --build
# API :8000, UI :8080
```

## CI

GitHub Actions on `main` / PRs: backend pytest + frontend typecheck/build/test.

---

## License

MIT.
