"""Pydantic models for Signal Loom API responses."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ReturnFormat(str, Enum):
    JSON = "json"
    TEXT = "text"
    SRT = "srt"
    VTT = "vtt"


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ─── Nested / component models ───────────────────────────────────────────────


class Word(BaseModel):
    """Individual word with timestamp and confidence."""

    word: str
    start: float
    end: float
    confidence: float = Field(ge=0.0, le=1.0)


class Sentiment(BaseModel):
    """Sentiment classification for a segment."""

    label: str  # e.g. "positive", "negative", "neutral"
    score: float = Field(ge=0.0, le=1.0)


class Topic(BaseModel):
    """Topic label with confidence score."""

    topic: str
    confidence: float = Field(ge=0.0, le=1.0)


class Entity(BaseModel):
    """Extracted entity within a segment."""

    type: str  # e.g. "PERSON", "ORGANIZATION", "LOCATION"
    text: str
    start: float
    end: float
    confidence: float = Field(ge=0.0, le=1.0)


class TranscriptSegment(BaseModel):
    """A single segment of a transcript.

    Field names are the SDK-internal names (the API response uses different names;
    the SDK's get_result() remaps them during deserialization).
    """

    id: Optional[str] = None       # remapped from segment_id
    start: Optional[float] = None  # remapped from start_seconds
    end: Optional[float] = None    # remapped from end_seconds
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    text: str
    translated_text: Optional[str] = None
    speaker: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    words: List[Word] = Field(default_factory=list)
    topics: List[Topic] = Field(default_factory=list)
    entities: List[Entity] = Field(default_factory=list)
    sentiment: Optional[Sentiment] = None


class Summary(BaseModel):
    """High-level summary of the transcript."""

    topics: List[Topic] = Field(default_factory=list)
    entities: List[Entity] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)


class TranscriptMetadata(BaseModel):
    """Metadata about the transcription job."""

    model: Optional[str] = None
    audio_duration: Optional[float] = None


class Transcript(BaseModel):
    """Complete transcription result."""

    job_id: str
    status: JobStatus
    language: Optional[str] = None
    duration_seconds: Optional[float] = None
    chars: Optional[int] = None
    text: Optional[str] = None  # raw text (also available via .text property)
    normalized_text: Optional[str] = None
    model: Optional[str] = None
    segments: List[TranscriptSegment] = Field(default_factory=list)
    summary: Optional[Summary] = None
    metadata: Optional[TranscriptMetadata] = None

    @property
    def transcript_text(self) -> str:
        """Return transcript text — prefers normalized_text if available."""
        if self.normalized_text:
            return self.normalized_text
        if self.text:
            return self.text
        return " ".join(seg.text for seg in self.segments)

    class Config:
        use_enum_values = True


class Job(BaseModel):
    """Transcription job state object."""

    job_id: str
    status: JobStatus
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    progress: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    class Config:
        use_enum_values = True


class HealthInfo(BaseModel):
    """Server health response."""

    status: str
    version: Optional[str] = None
    uptime: Optional[float] = None


class ServerInfo(BaseModel):
    """Server /v1/info response."""

    version: Optional[str] = None
    default_model: Optional[str] = None
    supported_models: Optional[List[str]] = None
    models: Optional[List[str]] = None
    capabilities: Optional[List[str]] = None
    max_concurrent_jobs: Optional[int] = None
    workspace: Optional[str] = None
    upload_dir: Optional[str] = None
    transcripts_dir: Optional[str] = None
