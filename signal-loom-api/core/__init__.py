# Signal Loom AI — API Service Core Configuration
"""
Environment-driven configuration for the Signal Loom API service.
All settings can be overridden via environment variables.

Priorities:
1. Environment variables (for production deployment)
2. .env file (for local development)
3. Defaults (for smoke testing without setup)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
WORKSPACE = Path(os.environ.get("WORKSPACE", "/Users/aehs-mini-ctrl/.openclaw/workspace"))
SIGNAL_LOOM_API_DIR = WORKSPACE / "signal-loom-api"
TRANSCRIPTS_DIR = WORKSPACE / "imports" / "media-agent" / "processed" / "transcripts"
RAW_LOCAL_AV_DIR = WORKSPACE / "imports" / "media-agent" / "raw" / "local-av"
VENV_PYTHON = WORKSPACE / ".venv-signal-loom-av" / "bin" / "python3"


# --------------------------------------------------------------------------- #
# Transcription defaults
# --------------------------------------------------------------------------- #
DEFAULT_MODEL = os.environ.get(
    "SIGNAL_LOOM_DEFAULT_MODEL",
    "mlx-community/whisper-large-v3-turbo"
)

SUPPORTED_MODELS = [
    "mlx-community/whisper-large-v3-turbo",
    "mlx-community/whisper-large-v3",
    "openai/whisper-large-v3",
]


# --------------------------------------------------------------------------- #
# Storage
# --------------------------------------------------------------------------- #
# Local filesystem for MVP; swap for S3/R2 in production
UPLOAD_DIR = SIGNAL_LOOM_API_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_SIZE_MB = int(os.environ.get("SIGNAL_LOOM_MAX_UPLOAD_MB", "500"))
ALLOWED_EXTENSIONS = {".mp3", ".mp4", ".m4a", ".wav", ".ogg", ".flac", ".mov", ".avi", ".mkv", ".webm"}


# --------------------------------------------------------------------------- #
# Workers
# --------------------------------------------------------------------------- #
# Number of concurrent transcription jobs
MAX_CONCURRENT_JOBS = int(os.environ.get("SIGNAL_LOOM_MAX_CONCURRENT_JOBS", "2"))

# Ollama endpoint for embedding/normalization (optional — uses local pipeline if not set)
OLLAMA_ENDPOINT = os.environ.get("OLLAMA_ENDPOINT", None)  # e.g. "http://192.168.1.182:11434"


# --------------------------------------------------------------------------- #
# Server
# --------------------------------------------------------------------------- #
HOST = os.environ.get("SIGNAL_LOOM_HOST", "0.0.0.0")
PORT = int(os.environ.get("SIGNAL_LOOM_PORT", "18790"))
DEBUG = os.environ.get("SIGNAL_LOOM_DEBUG", "false").lower() in ("true", "1", "yes")


# --------------------------------------------------------------------------- #
# Auth (MVP: free tier open; add API key auth for paid tiers)
# --------------------------------------------------------------------------- #
API_KEY_HEADER = os.environ.get("SIGNAL_LOOM_API_KEY_HEADER", "X-API-Key")
# Comma-separated list of valid API keys for paid tier
VALID_API_KEYS = [
    k.strip()
    for k in os.environ.get("SIGNAL_LOOM_VALID_API_KEYS", "").split(",")
    if k.strip()
]
REQUIRE_API_KEY = os.environ.get("SIGNAL_LOOM_REQUIRE_API_KEY", "false").lower() in ("true", "1", "yes")


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #
LOG_LEVEL = os.environ.get("SIGNAL_LOOM_LOG_LEVEL", "INFO").upper()
