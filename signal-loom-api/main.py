#!/usr/bin/env python3
"""
Signal Loom AI — FastAPI Service
Version: 0.1.0-alpha

Run:
  cd signal-loom-api
  pip install fastapi uvicorn python-multipart pydantic-settings httpx
  python -m uvicorn main:app --reload --port 18790 --host 0.0.0.0
"""

from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from core import (
    SIGNAL_LOOM_API_DIR,
    UPLOAD_DIR,
    TRANSCRIPTS_DIR,
    DEFAULT_MODEL,
    SUPPORTED_MODELS,
    MAX_CONCURRENT_JOBS,
    HOST,
    PORT,
    DEBUG,
    REQUIRE_API_KEY,
    API_KEY_HEADER,
    VALID_API_KEYS,
    WORKSPACE,
)
from jobs import jobs, JobStatus
from starlette.middleware.authentication import AuthenticationMiddleware
from middleware.auth import BearerAuthBackend, auth_on_error
from schemas import HealthResponse
from routers import health, transcribe, models, admin
from monitoring import metrics
from webhooks.api_keys import api_keys, KeyTier, TIERS as KEY_TIERS

# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
log = logging.getLogger("signal-loom-api")

# --------------------------------------------------------------------------- #
# Lifespan
# --------------------------------------------------------------------------- #
start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Signal Loom AI API starting up...")
    log.info(f"  Upload dir:    {UPLOAD_DIR}")
    log.info(f"  Transcripts:  {TRANSCRIPTS_DIR}")
    log.info(f"  Workspace:    {WORKSPACE}")
    log.info(f"  Max concurrent jobs: {MAX_CONCURRENT_JOBS}")
    log.info(f"  Default model: {DEFAULT_MODEL}")
    log.info(f"  API auth:     {'required' if REQUIRE_API_KEY else 'open'}")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    yield
    log.info("Signal Loom AI API shutting down...")


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #
app = FastAPI(
    title="Signal Loom AI API",
    description=(
        "Transcription pipeline API — turns video and audio into structured, "
        "language-agnostic, agent-readable knowledge objects. "
        "Built for AI agents, developer tools, and RAG pipelines."
    ),
    version="0.1.0-alpha",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — open for MVP, tighten for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key auth middleware
app.add_middleware(
    AuthenticationMiddleware,
    backend=BearerAuthBackend(),
    on_error=auth_on_error,
)


# --------------------------------------------------------------------------- #
# Optional API key auth dependency
# --------------------------------------------------------------------------- #
def verify_api_key(x_api_key: Optional[str] = None) -> Optional[str]:
    if not REQUIRE_API_KEY:
        return None
    if x_api_key is None:
        raise HTTPException(status_code=401, detail="API key required")
    if VALID_API_KEYS and x_api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key


# --------------------------------------------------------------------------- #
# Mount static / docs
# --------------------------------------------------------------------------- #
_docs_dir = SIGNAL_LOOM_API_DIR / "static"
if _docs_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_docs_dir)), name="static")


# --------------------------------------------------------------------------- #
# Routers
# --------------------------------------------------------------------------- #
app.include_router(health.router, tags=["Health"])
app.include_router(transcribe.router, prefix="/v1", tags=["Transcription"])
app.include_router(models.router, tags=["Models"])
app.include_router(admin.router, prefix="/v1", tags=["Admin"])


# --------------------------------------------------------------------------- #
# Root
# --------------------------------------------------------------------------- #
@app.get("/", response_class=PlainTextResponse)
def root():
    return "Signal Loom AI API — /docs for interactive API explorer"


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    """Public health check — no auth required."""
    return HealthResponse(
        status="ok",
        version="0.1.0-alpha",
        uptime_seconds=round(time.time() - start_time, 2),
        queue_size=len(jobs.all()),
        active_jobs=jobs.count_active(),
        max_concurrent_jobs=MAX_CONCURRENT_JOBS,
        storage_used_mb=None,
        models_available=SUPPORTED_MODELS,
    )


# --------------------------------------------------------------------------- #
# Error handlers
# --------------------------------------------------------------------------- #
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    log.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc) if DEBUG else None},
    )


# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #
def main():
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG,
        log_level="info",
    )


if __name__ == "__main__":
    main()
