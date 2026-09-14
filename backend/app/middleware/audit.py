"""Lightweight request audit logging (metadata / ids only)."""

from __future__ import annotations

import time

from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings
from app.database import SessionLocal
from app.models import RequestLog

SKIP_PREFIXES = ("/health", "/ready", "/docs", "/openapi", "/redoc", "/favicon")


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:  # noqa: ANN001
        path = request.url.path
        if any(path.startswith(p) for p in SKIP_PREFIXES):
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)

        actor_id = None
        org_id = None
        auth = request.headers.get("authorization") or ""
        if auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1].strip()
            try:
                payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
                actor_id = int(payload.get("sub")) if payload.get("sub") else None
                org_id = int(payload.get("org_id")) if payload.get("org_id") is not None else None
            except (JWTError, ValueError, TypeError):
                pass

        try:
            db = SessionLocal()
            db.add(
                RequestLog(
                    method=request.method[:16],
                    path=path[:255],
                    status_code=response.status_code,
                    actor_user_id=actor_id,
                    org_id=org_id,
                    duration_ms=duration_ms,
                )
            )
            db.commit()
        except Exception:
            # Never break the request for audit failures
            pass
        finally:
            try:
                db.close()
            except Exception:
                pass

        return response
