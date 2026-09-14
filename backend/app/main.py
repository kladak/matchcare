"""MatchCare FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.middleware.audit import AuditMiddleware
from app.routers import admin, auth, health, match, match_requests, providers
from app.seed import seed_if_empty


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    if settings.seed_on_startup:
        db = SessionLocal()
        try:
            seed_if_empty(db)
        finally:
            db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        "Clean-room multi-tenant specialty matching demo (portfolio). "
        "Not affiliated with SpeciaList Health. Synthetic data only — no HIPAA claims."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuditMiddleware)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(providers.router)
app.include_router(match.router)
app.include_router(match_requests.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {
        "service": "matchcare",
        "docs": "/docs",
        "health": "/health",
        "disclaimer": "Educational portfolio demo — synthetic data only.",
    }
