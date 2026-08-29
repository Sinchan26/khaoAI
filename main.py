"""khaoAI — single-server entry point.

Assembles the FastAPI app, loads mock data at startup, registers all API
routes, and serves the demo frontend as static files at ``/``.

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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from wrapper.log import setup_logging

# Configure structured logging first
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))

from wrapper.log import get_logger
from wrapper.routes import auth, chat, config, debug

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


# ---------------------------------------------------------------------------
# Lifespan — load mock data once at startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    from mocks.store import load as load_mocks
    _log.info("Loading mock food-delivery data...")
    await load_mocks()
    _log.info("khaoAI ready — open http://localhost:8000")
    yield


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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(auth.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(debug.router, prefix="/api")


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "khaoAI (single-server)",
    }


# Serve the frontend at / (mounted last so API routes take priority)
_frontend_dir = Path(__file__).parent / "frontend"
if _frontend_dir.is_dir():
    app.mount("/", NoCacheStaticFiles(directory=_frontend_dir, html=True), name="frontend")
