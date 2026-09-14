# MatchCare

**Karim Ladak · portfolio / educational project**

Multi-tenant **specialty matching** SaaS demo: patients get ranked providers by specialty preference, location, subscription/access tier, and capacity — with explainable score breakdowns. Providers and tenant admins see the other side of the funnel.

## Scope & honesty

Clean-room educational implementation using synthetic data. Demo JWT auth (one-click personas). Audit logs are metadata / ids only — never clinical content or real PHI. Not a production healthcare product.

See [`PROVENANCE.md`](PROVENANCE.md) for affiliation notes. Full formula and architecture: [`SPEC.md`](SPEC.md).

---

## Demo script (60–90s)

Cold start — exact clicks for a recruiter walkthrough or screen recording.

### 0. Prerequisites (once)

```bash
git clone https://github.com/kladak/matchcare.git
cd matchcare

# Terminal A — API
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal B — dashboard
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**.

### 1. Patient match (~40s)

1. Read the disclaimer banner (synthetic / educational).
2. On **Demo login**, click **Continue as Patient** (Ava Chen).
3. Land on **Find matches** — preferred specialties and city pre-filled from seed.
4. Click **Run match**. Show the ranked list with **overall score** and breakdown chips (specialty / location / tier / availability).
5. Expand one row — call out the formula weights briefly (40% specialty, 25% location, 20% tier, 15% availability).
6. Click **Request match** on the top result → success toast; note it appears under **My requests**.

### 2. Provider inbox (~20s)

1. **Sign out** → **Continue as Provider** (Dr. Sam Okonkwo).
2. Open **Inbox** — see inbound match requests for your profile.
3. **Accept** one → status updates; optional **Propose appointment**.

### 3. Admin tenant (~20s)

1. **Sign out** → **Continue as Admin** (Morgan Park).
2. **Tenant overview** — org name, subscription tier, counts (patients / providers / open requests).
3. Glance at **Audit log** — method, path, status, actor id (no bodies).
4. Optional: mention second tenant (`summit`) for isolation — login with summit personas from `/auth/personas`.

### 4. Close (~10s)

1. Hit **http://localhost:8000/docs** — typed OpenAPI.
2. `curl localhost:8000/health` and `/ready`.
3. Reminder: portfolio demo; local run is the source of truth today.

---

## Architecture

| Layer | Stack |
|-------|--------|
| API | FastAPI, SQLAlchemy, SQLite, JWT (demo), seed on startup |
| Matching | Weighted specialty · location · tier · availability (see SPEC) |
| UI | Vite + React + TypeScript |
| Roles | `patient` · `provider` · `admin` (org-scoped) |
| CI | GitHub Actions (pytest + frontend build/test) |
| Optional | `docker compose up` |

```
frontend (Vite)  →  FastAPI + JWT  →  SQLite seed store
                         └── matching service + audit middleware
```

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

See Demo script §0 above.

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
# API :8000  ·  UI :8080
```

## CI

GitHub Actions on `main` / PRs: backend pytest + frontend typecheck/build/test.

---

## License

MIT — portfolio / educational use.
