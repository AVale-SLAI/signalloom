# Signal Loom AI — API Schemas
"""
Pydantic schemas for the Signal Loom API.
Defines all request/response shapes for type safety and OpenAPI generation.

Python 3.9 compatible — use Optional[X] and Union[X, Y] instead of X | Y syntax.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional, Union, Dict

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #
class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class MediaKind(str, Enum):
    AUDIO = "audio"
    VIDEO = "video"
    UNKNOWN = "unknown"


# --------------------------------------------------------------------------- #
# Shared
# --------------------------------------------------------------------------- #
class TranscriptSegment(BaseModel):
    segment_id: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    start_seconds: Optional[float] = None
    end_seconds: Optional[float] = None
    text: str
    translated_text: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    words: Optional[List[Dict[str, Any]]] = None


class TranscriptOutput(BaseModel):
    title: str
    source_ref: str
    source_kind: str = "local_av"
    media_kind: str
    language: Optional[str] = None
    model: str
    created_at: str
    duration_seconds: Optional[float] = None
    normalized_text: str
    text: str
    segments: List[TranscriptSegment]
    metadata: Dict[str, Any] = Field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Request models
# --------------------------------------------------------------------------- #
class TranscribeRequest(BaseModel):
    """
    Request to transcribe a media file.
    """
    url: Optional[str] = Field(default=None, description="Public URL to audio/video file to transcribe")
    language: Optional[str] = Field(default=None, description="Force language code (e.g. 'en', 'zh', 'auto'). Default: auto-detect.")
    model: Optional[str] = Field(default=None, description="Model to use. Default: mlx-community/whisper-large-v3-turbo")
    word_timestamps: bool = Field(default=False, description="Include per-word timestamps")
    webhook_url: Optional[str] = Field(default=None, description="Optional webhook URL to POST completion notification")
    normalize: bool = Field(default=True, description="Return normalized Signal Loom knowledge object format")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "url": "https://example.com/video.mp4",
                    "language": "auto",
                    "model": "mlx-community/whisper-large-v3-turbo",
                    "word_timestamps": False,
                }
            ]
        }
    }


class TranscribeResponse(BaseModel):
    job_id: str = Field(description="Unique job ID for tracking and retrieval")
    status: JobStatus
    created_at: str
    message: Optional[str] = None


class StatusResponse(BaseModel):
    job_id: str
    status: JobStatus
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    language: Optional[str] = None
    model: Optional[str] = None
    duration_seconds: Optional[float] = None
    chars: Optional[int] = None
    segments: Optional[int] = None
    error: Optional[str] = None
    retry_count: Optional[int] = None
    elapsed_seconds: Optional[float] = None
    result_url: Optional[str] = Field(default=None, description="URL to retrieve transcript (GET /result/{job_id})")


class ResultResponse(BaseModel):
    job_id: str
    status: JobStatus
    # Free-form transcript object — structure matches the transcription pipeline output
    # See API_SCHEMA.md for full documentation
    transcript: Optional[Dict[str, Any]] = None
    raw_text: Optional[str] = None
    srt: Optional[str] = None
    vtt: Optional[str] = None
    download_url: Optional[str] = None


class HealthResponse(BaseModel):
    status: str  # Literal["ok", "degraded", "down"]
    version: str
    uptime_seconds: float
    queue_size: int
    active_jobs: int
    max_concurrent_jobs: int
    storage_used_mb: Optional[float] = None
    models_available: List[str]


class ModelsResponse(BaseModel):
    models: List[Dict[str, Any]]


# --------------------------------------------------------------------------- #
# Error
# --------------------------------------------------------------------------- #
class APIError(BaseModel):
    error: str
    detail: Optional[str] = None
    job_id: Optional[str] = None


class LimitsResponse(BaseModel):
    """Current rate limit status for the authenticated API key."""
    tier: str
    key_id: str
    daily_limit: int = Field(description="Max requests per day (-1 = unlimited)")
    daily_used: int
    daily_remaining: int = Field(description="-1 = unlimited")
    daily_reset_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp when the daily window resets"
    )
    minute_limit: int = Field(description="Max requests per minute (-1 = unlimited)")
    minute_used: int
    minute_remaining: int = Field(description="-1 = unlimited")
    minute_reset_at: Optional[str] = Field(
        default=None,
        description="ISO timestamp when the minute window resets"
    )
    monthly_audio_minutes_limit: int = Field(
        description="Max billable audio minutes per month (-1 = unlimited)"
    )
    monthly_audio_minutes_used: int
