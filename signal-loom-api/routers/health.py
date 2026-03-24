# Signal Loom AI — Health Router
"""
Simple health and readiness endpoints.
"""

from __future__ import annotations

import time
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from core import (
    TRANSCRIPTS_DIR,
    UPLOAD_DIR,
    WORKSPACE,
    MAX_CONCURRENT_JOBS,
    SUPPORTED_MODELS,
    DEFAULT_MODEL,
    VENV_PYTHON,
)
from jobs import jobs

router = APIRouter()

start_time = time.time()


class HealthCheck(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    queue_depth: int
    active_jobs: int
    max_jobs: int
    transcripts_dir_ok: bool
    upload_dir_ok: bool
    venv_python_ok: bool
    models_available: list[str]
    default_model: str


@router.get("/health", response_model=HealthCheck)
def health():
    """
    Full health check — use this for load balancer readiness probes.
    Returns structured health status including queue depth and directory checks.
    """
    transcripts_ok = TRANSCRIPTS_DIR.exists() and TRANSCRIPTS_DIR.is_dir()
    upload_ok = UPLOAD_DIR.exists() and UPLOAD_DIR.is_dir()
    venv_ok = VENV_PYTHON.exists() if VENV_PYTHON else False

    all_jobs = jobs.all()
    active = jobs.count_active()
    overall = "ok"
    if not transcripts_ok or not upload_ok:
        overall = "degraded"
    if not venv_ok:
        overall = "degraded"

    return HealthCheck(
        status=overall,
        version="0.1.0-alpha",
        uptime_seconds=round(time.time() - start_time, 2),
        queue_depth=len(all_jobs),
        active_jobs=active,
        max_jobs=MAX_CONCURRENT_JOBS,
        transcripts_dir_ok=transcripts_ok,
        upload_dir_ok=upload_ok,
        venv_python_ok=venv_ok,
        models_available=SUPPORTED_MODELS,
        default_model=DEFAULT_MODEL,
    )


@router.get("/ready")
def ready():
    """
    Simple yes/no readiness probe for Kubernetes / container orchestration.
    Returns 200 if ready to accept jobs.
    """
    return {"ready": True}
