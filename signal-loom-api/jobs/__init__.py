# Signal Loom AI — Job Manager
"""
In-memory job state management for MVP.
Each job tracks: status, metadata, result, error.

For production, swap for Redis/Postgres.
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# --------------------------------------------------------------------------- #
# Job state
# --------------------------------------------------------------------------- #
# Whisper-supported language codes (ISO 639-1)
VALID_LANGUAGE_CODES = {
    "en", "es", "fr", "de", "it", "pt", "pl", "nl", "ja", "zh",
    "ko", "ru", "ar", "hi", "tr", "vi", "th", "id", "ms", "cs",
    "el", "he", "ro", "uk", "hu", "fi", "sv", "da", "no", "bg",
    "hr", "sk", "sl", "et", "lv", "lt", "fa", "ta", "te", "bn",
    "ml", "mr", "ur", "gu", "kn", "pa", "ne", "si", "my", "km",
    "lo", "jw", "su", "ca", "eu", "gl", "is", "mk", "sr", "bs",
    # Auto-detect (let Whisper figure it out)
    "auto", "none", "",
}

class JobStatus:
    """Simple string-based job status enum."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

    @classmethod
    def values(cls) -> list:
        return [cls.QUEUED, cls.PROCESSING, cls.COMPLETED, cls.FAILED]


class Job:
    __slots__ = (
        "job_id", "status", "created_at", "started_at", "completed_at",
        "language", "model", "duration_seconds", "chars", "segments",
        "error", "retry_count", "elapsed_seconds",
        "source_url", "source_path", "word_timestamps", "webhook_url", "return_format",
        "transcript_json_path", "raw_text", "srt", "vtt", "transcript_obj",
        "api_key_id",
    )

    def __init__(
        self,
        job_id: str,
        status: str = "queued",
        created_at: Optional[str] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        language: Optional[str] = None,
        model: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        chars: Optional[int] = None,
        segments: Optional[int] = None,
        error: Optional[str] = None,
        retry_count: int = 0,
        elapsed_seconds: Optional[float] = None,
        source_url: Optional[str] = None,
        source_path: Optional[str] = None,
        word_timestamps: bool = False,
        webhook_url: Optional[str] = None,
        return_format: str = "json",
        transcript_json_path: Optional[str] = None,
        raw_text: Optional[str] = None,
        srt: Optional[str] = None,
        vtt: Optional[str] = None,
        transcript_obj: Optional[Dict[str, Any]] = None,
        api_key_id: Optional[str] = None,
    ) -> None:
        self.job_id = job_id
        self.status = status
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.started_at = started_at
        self.completed_at = completed_at
        self.language = language
        self.model = model
        self.duration_seconds = duration_seconds
        self.chars = chars
        self.segments = segments
        self.error = error
        self.retry_count = retry_count
        self.elapsed_seconds = elapsed_seconds
        self.source_url = source_url
        self.source_path = source_path
        self.word_timestamps = word_timestamps
        self.webhook_url = webhook_url
        self.return_format = return_format
        self.transcript_json_path = transcript_json_path
        self.raw_text = raw_text
        self.srt = srt
        self.vtt = vtt
        self.transcript_obj = transcript_obj
        self.api_key_id = api_key_id

    def to_status_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "language": self.language,
            "model": self.model,
            "duration_seconds": self.duration_seconds,
            "chars": self.chars,
            "segments": self.segments,
            "error": self.error,
            "retry_count": self.retry_count,
            "elapsed_seconds": self.elapsed_seconds,
            "result_url": f"/v1/result/{self.job_id}" if self.status == "completed" else None,
        }

    def to_result_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "transcript": self.transcript_obj,
            "raw_text": self.raw_text,
            "srt": self.srt,
            "vtt": self.vtt,
        }


# --------------------------------------------------------------------------- #
# JobManager — thread-safe in-memory store
# --------------------------------------------------------------------------- #
class JobManager:
    """
    Thread-safe in-memory job store.

    For production, replace with Redis + Postgres for:
    - persistence across restarts
    - distributed queue across workers
    - job TTL management
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._jobs: Dict[str, Job] = {}

    def create(self, **kwargs) -> Job:
        job_id = kwargs.pop("job_id", None) or str(uuid.uuid4())[:8]
        job = Job(job_id=job_id, **kwargs)
        with self._lock:
            self._jobs[job_id] = job
        return job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **updates) -> Optional[Job]:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            for key, value in updates.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            return job

    def list_active(self) -> List[Job]:
        with self._lock:
            return [
                j for j in self._jobs.values()
                if j.status in (JobStatus.QUEUED, JobStatus.PROCESSING)
            ]

    def count_active(self) -> int:
        with self._lock:
            return sum(
                1 for j in self._jobs.values()
                if j.status in (JobStatus.QUEUED, JobStatus.PROCESSING)
            )

    def all(self) -> Dict[str, Job]:
        with self._lock:
            return dict(self._jobs)


# Singleton
jobs = JobManager()
