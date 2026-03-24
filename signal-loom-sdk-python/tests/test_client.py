"""Tests for Signal Loom SDK client."""

from __future__ import annotations

import json
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from signalloom import SignalLoom
from signalloom.errors import (
    InvalidRequestError,
    JobFailedError,
    RateLimitError,
    SignalLoomError,
    TimeoutError,
)
from signalloom.models import Job, JobStatus, Transcript, TranscriptSegment


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def client() -> Generator[SignalLoom, None, None]:
    """Return a SignalLoom client pointed at a test base URL."""
    with SignalLoom(base_url="http://localhost:18790") as c:
        yield c


@pytest.fixture
def mock_httpx_success(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch httpx.Client.request to return successful responses."""
    mock_response = MagicMock()
    mock_response.is_success = True
    mock_response.status_code = 200
    mock_response.json.return_value = {}
    mock_response.text = ""

    mock_client = MagicMock()
    mock_client.request.return_value = mock_response

    # Patch the class so SignalLoom._http returns our mock
    import httpx
    with patch.object(httpx, "Client", return_value=mock_client):
        yield mock_client


# ─── Health ───────────────────────────────────────────────────────────────────

def test_health_returns_dict(client: SignalLoom) -> None:
    """Health endpoint returns a dictionary."""
    with patch.object(client, "_request") as mock_req:
        mock_req.return_value.json.return_value = {
            "status": "ok",
            "version": "0.1.0-alpha",
        }
        health = client.health
        assert health["status"] == "ok"
        assert "version" in health


# ─── Transcription job submission ─────────────────────────────────────────────

def test_transcribe_with_url(client: SignalLoom) -> None:
    """transcribe() accepts a URL and returns a Job."""
    with patch.object(client, "_request") as mock_req:
        mock_req.return_value.json.return_value = {
            "job_id": "abc123",
            "status": "queued",
        }
        mock_req.return_value.is_success = True
        mock_req.return_value.status_code = 200

        job = client.transcribe(url="https://example.com/audio.mp3")
        assert job.job_id == "abc123"
        assert job.status == "queued"

        # Verify URL was passed in the request
        call_kwargs = mock_req.call_args.kwargs
        assert call_kwargs["data"]["url"] == "https://example.com/audio.mp3"


def test_transcribe_requires_file_or_url(client: SignalLoom) -> None:
    """transcribe() raises InvalidRequestError if neither file nor url given."""
    with pytest.raises(InvalidRequestError):
        client.transcribe()  # type: ignore[call-arg]


def test_transcribe_rejects_both_file_and_url(client: SignalLoom) -> None:
    """transcribe() raises InvalidRequestError if both file and url given."""
    with pytest.raises(InvalidRequestError):
        client.transcribe(file="audio.mp3", url="https://example.com/audio.mp3")


# ─── get_job / get_result ─────────────────────────────────────────────────────

def test_get_job_returns_job(client: SignalLoom) -> None:
    """get_job() returns a Job object."""
    with patch.object(client, "_request") as mock_req:
        mock_req.return_value.json.return_value = {
            "job_id": "abc123",
            "status": "processing",
            "progress": 0.45,
        }

        job = client.get_job("abc123")
        assert isinstance(job, Job)
        assert job.job_id == "abc123"


def test_get_result_returns_transcript(client: SignalLoom) -> None:
    """get_result() returns a Transcript object."""
    with patch.object(client, "_request") as mock_req:
        mock_req.return_value.json.return_value = {
            "job_id": "abc123",
            "status": "completed",
            "language": "en",
            "duration_seconds": 123.4,
            "chars": 1500,
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 5.0,
                    "text": "Hello world",
                    "speaker": "SPEAKER_1",
                    "words": [
                        {"word": "Hello", "start": 0.0, "end": 0.5, "confidence": 0.99},
                        {"word": "world", "start": 0.5, "end": 1.0, "confidence": 0.98},
                    ],
                    "topics": [{"topic": "greeting", "confidence": 0.92}],
                    "entities": [],
                    "sentiment": {"label": "positive", "score": 0.87},
                }
            ],
            "summary": {
                "topics": [{"topic": "greeting", "confidence": 0.92}],
                "entities": [],
                "keywords": ["hello", "world"],
            },
            "metadata": {
                "model": "mlx-community/whisper-large-v3-turbo",
                "audio_duration": 123.4,
            },
        }
        mock_req.return_value.is_success = True
        mock_req.return_value.status_code = 200

        result = client.get_result("abc123")
        assert isinstance(result, Transcript)
        assert result.job_id == "abc123"
        assert result.status == "completed"
        assert result.segments[0].speaker == "SPEAKER_1"
        assert result.segments[0].words[0].word == "Hello"
        assert result.segments[0].sentiment.label == "positive"


# ─── Error handling ───────────────────────────────────────────────────────────

def test_rate_limit_error(client: SignalLoom) -> None:
    """HTTP 429 raises RateLimitError."""
    with patch.object(client, "_request") as mock_req:
        mock_resp = MagicMock()
        mock_resp.is_success = False
        mock_resp.status_code = 429
        mock_resp.text = "Rate limit exceeded"
        mock_req.return_value = mock_resp

        with pytest.raises(RateLimitError) as exc_info:
            client.transcribe(url="https://example.com/audio.mp3")
        assert exc_info.value.status_code == 429


def test_invalid_request_error(client: SignalLoom) -> None:
    """HTTP 400 raises InvalidRequestError."""
    with patch.object(client, "_request") as mock_req:
        mock_resp = MagicMock()
        mock_resp.is_success = False
        mock_resp.status_code = 400
        mock_resp.text = "Bad request"
        mock_req.return_value = mock_resp

        with pytest.raises(InvalidRequestError):
            client.transcribe(url="https://example.com/audio.mp3")


# ─── cancel_job ───────────────────────────────────────────────────────────────

def test_cancel_job_returns_true_on_success(client: SignalLoom) -> None:
    """cancel_job() returns True when the server accepts the cancellation."""
    with patch.object(client, "_request") as mock_req:
        mock_resp = MagicMock()
        mock_resp.is_success = True
        mock_resp.status_code = 200
        mock_req.return_value = mock_resp

        result = client.cancel_job("abc123")
        assert result is True


def test_cancel_job_returns_false_when_not_found(client: SignalLoom) -> None:
    """cancel_job() returns False when the job does not exist."""
    with patch.object(client, "_request") as mock_req:
        mock_resp = MagicMock()
        mock_resp.is_success = False
        mock_resp.status_code = 404
        mock_req.return_value = mock_resp

        result = client.cancel_job("nonexistent")
        assert result is False


# ─── Transcript.text property ─────────────────────────────────────────────────

def test_transcript_text_concatenates_segments() -> None:
    """Transcript.text returns space-joined segment texts."""
    data = {
        "job_id": "j1",
        "status": "completed",
        "segments": [
            {"id": 0, "start": 0.0, "end": 1.0, "text": "Hello", "speaker": None, "words": [], "topics": [], "entities": []},
            {"id": 1, "start": 1.0, "end": 2.0, "text": "world", "speaker": None, "words": [], "topics": [], "entities": []},
        ],
    }
    t = Transcript(**data)
    assert t.text == "Hello world"


# ─── Timeout error ────────────────────────────────────────────────────────────

def test_timeout_error_raised(client: SignalLoom) -> None:
    """TimeoutError is raised when sync transcription times out."""
    with patch.object(client, "_request") as mock_req:
        # First call: submit job
        submit_resp = MagicMock()
        submit_resp.is_success = True
        submit_resp.status_code = 200
        submit_resp.json.return_value = {"job_id": "abc123", "status": "queued"}

        # Second call: get job status → still processing
        status_resp = MagicMock()
        status_resp.is_success = True
        status_resp.status_code = 200
        status_resp.json.return_value = {"job_id": "abc123", "status": "processing", "progress": 0.5}

        mock_req.side_effect = [submit_resp, status_resp]

        # Use a very short timeout to force the error quickly
        with pytest.raises(TimeoutError):
            client.transcribe_sync(
                url="https://example.com/audio.mp3",
                timeout=1,  # 1 second should trigger timeout in the mock loop
            )


# ─── list_jobs ────────────────────────────────────────────────────────────────

def test_list_jobs_returns_list(client: SignalLoom) -> None:
    """list_jobs() returns a list of Job objects."""
    with patch.object(client, "_request") as mock_req:
        mock_req.return_value.json.return_value = [
            {"job_id": "j1", "status": "completed"},
            {"job_id": "j2", "status": "processing"},
        ]
        mock_req.return_value.is_success = True
        mock_req.return_value.status_code = 200

        jobs = client.list_jobs()
        assert len(jobs) == 2
        assert all(isinstance(j, Job) for j in jobs)
