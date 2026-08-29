"""khaoAI — single-server entry point.

Assembles the FastAPI app, database, read-only Swiggy provider routes, agent,
and static frontend.

Run:  uvicorn main:app --port 8000 --reload
"""
from __future__ import annotations

import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # load .env before anything reads os.getenv

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

from wrapper.log import setup_logging

# Configure structured logging first
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))

from wrapper.log import get_logger
from wrapper.db import get_db_session
from wrapper.config import settings
from wrapper.routes import auth, chat, config, debug, providers

_log = get_logger("api")


# ---------------------------------------------------------------------------
# No-cache static files (same pattern as UCP-Funnel)
# ---------------------------------------------------------------------------

class NoCacheStaticFiles(StaticFiles):
    """Force revalidation so browsers don't serve stale JS/CSS after edits."""

    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-cache"
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; "
            "connect-src 'self' ws: wss:; frame-ancestors 'none'"
        )
        return response


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    from wrapper.db import close_database, init_database
    await init_database()
    if settings.fixture_provider_enabled:
        from mocks.store import load as load_mocks
        _log.info("Loading test fixture food data...")
        await load_mocks()
    _log.info("khaoAI ready — open http://localhost:8000")
    try:
        yield
    finally:
        await close_database()


# ---------------------------------------------------------------------------
# App assembly
# ---------------------------------------------------------------------------

app = FastAPI(
    title="khaoAI",
    description="Agentic food concierge — single-server architecture",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)

# API routes
app.include_router(auth.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(debug.router, prefix="/api")
app.include_router(providers.router, prefix="/api")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "khaoAI (single-server)",
        "provider": "swiggy-read-only",
        "fixture_provider": settings.fixture_provider_enabled,
    }


@app.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db_session)):
    try:
        await db.execute(sql_text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from exc
    return {"status": "ready", "database": "connected"}


# Serve the frontend at / (mounted last so API routes take priority)
_frontend_dir = Path(__file__).parent / "frontend"
if _frontend_dir.is_dir():
    app.mount("/", NoCacheStaticFiles(directory=_frontend_dir, html=True), name="frontend")
