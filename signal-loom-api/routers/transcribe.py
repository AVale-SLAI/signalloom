# Signal Loom AI — Transcription Router
"""
POST /v1/transcribe — Submit a transcription job
GET  /v1/status/{job_id} — Check job status
GET  /v1/result/{job_id} — Get transcript result
GET  /v1/jobs — List all jobs (admin/debug)
DELETE /v1/job/{job_id} — Cancel/delete a job
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, Request
from fastapi.responses import FileResponse, PlainTextResponse

from core import (
    UPLOAD_DIR,
    TRANSCRIPTS_DIR,
    RAW_LOCAL_AV_DIR,
    DEFAULT_MODEL,
    SUPPORTED_MODELS,
    MAX_CONCURRENT_JOBS,
    MAX_UPLOAD_SIZE_MB,
    ALLOWED_EXTENSIONS,
    WORKSPACE,
    VENV_PYTHON,
)
from jobs import jobs, JobStatus
from monitoring import metrics
from schemas import (
    TranscribeResponse,
    StatusResponse,
    ResultResponse,
    APIError,
    LimitsResponse,
)


# --------------------------------------------------------------------------- #
# SSRF Protection — block internal/private network ranges
# --------------------------------------------------------------------------- #
import ipaddress

PRIVATE_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),   # link-local (AWS metadata)
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("100.64.0.0/10"),   # CGN shared
    ipaddress.ip_network("192.0.0.0/24"),
    ipaddress.ip_network("192.0.2.0/24"),   # TEST-NET-1
    ipaddress.ip_network("198.51.100.0/24"), # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),  # TEST-NET-3
]

BLOCKED_HOSTS = {
    "localhost", "localhost.localdomain",
    "0.0.0.0", "::1",
    "metadata.google.internal",      # GCP metadata
    "169.254.169.254",               # AWS/Azure metadata
    "metadata.internal",
}


def is_url_safe(url_str: str) -> bool:
    """
    Block URLs that resolve to private/internal network addresses.
    Prevents SSRF attacks via DNS rebinding or redirects.
    """
    try:
        parsed = urllib.parse.urlparse(url_str)
        hostname = parsed.hostname or ""
        port = parsed.port

        # Check hostname
        if hostname.lower() in BLOCKED_HOSTS:
            return False

        # Resolve hostname to IP and check ranges
        try:
            sock = socket.socket()
            sock.settimeout(2.0)
            socket.getaddrinfo(hostname, port or 80, socket.AF_UNSPEC, socket.SOCK_STREAM)
        except Exception:
            return True  # Can't resolve — let it fail naturally later

        # Check IPv4
        try:
            ip = socket.gethostbyname(hostname)
            addr = ipaddress.ip_address(ip)
            for net in PRIVATE_RANGES:
                if addr in net:
                    return False
        except Exception:
            pass

        return True
    except Exception:
        return True  # Fail open on parse errors — let it fail at download time


router = APIRouter()

TRANSCRIBE_SCRIPT = WORKSPACE / "scripts" / "transcribe_local_media.py"


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _job_to_status_response(job) -> StatusResponse:
    return StatusResponse(
        job_id=job.job_id,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        language=job.language,
        model=job.model,
        duration_seconds=job.duration_seconds,
        chars=job.chars,
        segments=job.segments,
        error=job.error,
        retry_count=job.retry_count,
        elapsed_seconds=job.elapsed_seconds,
        result_url=f"/v1/result/{job.job_id}" if job.status == JobStatus.COMPLETED else None,
    )


def _job_to_result_response(job) -> ResultResponse:
    transcript_obj = None

    # First check in-memory transcript object (fastest path)
    if job.transcript_obj:
        transcript_obj = job.transcript_obj

    # Second: try stored path from job
    elif job.transcript_json_path:
        p = Path(job.transcript_json_path)
        if p.exists():
            try:
                with open(p) as f:
                    transcript_obj = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

    # Third: glob for any transcript file with this job_id as prefix
    # (handles case where pipeline named file with job_id prefix)
    if transcript_obj is None:
        for p in TRANSCRIPTS_DIR.glob(f"{job.job_id}*.transcript.json"):
            try:
                with open(p) as f:
                    transcript_obj = json.load(f)
                    break
            except (json.JSONDecodeError, OSError):
                continue

    return ResultResponse(
        job_id=job.job_id,
        status=job.status,
        transcript=transcript_obj,
        raw_text=job.raw_text,
        srt=job.srt,
        vtt=job.vtt,
        download_url=f"/v1/download/{job.job_id}" if job.status == JobStatus.COMPLETED else None,
    )


async def _run_transcription_job(job_id: str) -> None:
    """Background worker: runs the transcription pipeline for a queued job."""
    job = jobs.get(job_id)
    if not job:
        return

    jobs.update(job_id, status=JobStatus.PROCESSING, started_at=datetime.now(timezone.utc).isoformat())

    try:
        cmd = [
            str(VENV_PYTHON),
            str(TRANSCRIBE_SCRIPT),
            job.source_path or "",
            "--model", job.model or DEFAULT_MODEL,
            "--json-status",
        ]
        if job.word_timestamps:
            cmd.append("--word-timestamps")
        if job.return_format in ("srt", "vtt", "txt"):
            cmd.extend(["--return-format", job.return_format])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=3600,
        )

        if result.returncode == 0:
            try:
                output = json.loads(result.stdout)
                jobs.update(
                    job_id,
                    status=JobStatus.COMPLETED,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                    language=output.get("language"),
                    model=output.get("model"),
                    duration_seconds=output.get("duration_seconds"),
                    chars=output.get("chars", 0),
                    segments=output.get("segments", 0),
                    elapsed_seconds=output.get("elapsed_seconds", 0.0),
                    transcript_json_path=output.get("transcript_json"),
                )
            except json.JSONDecodeError:
                jobs.update(
                    job_id,
                    status=JobStatus.COMPLETED,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                    elapsed_seconds=0.0,
                )
        else:
            error_msg = result.stderr or f"exit code {result.returncode}"
            try:
                err_output = json.loads(result.stdout)
                error_msg = err_output.get("error", error_msg)
            except Exception:
                pass
            jobs.update(
                job_id,
                status=JobStatus.FAILED,
                completed_at=datetime.now(timezone.utc).isoformat(),
                error=error_msg,
            )

    except subprocess.TimeoutExpired:
        jobs.update(
            job_id,
            status=JobStatus.FAILED,
            completed_at=datetime.now(timezone.utc).isoformat(),
            error="Transcription timed out after 1 hour",
        )
    except Exception as exc:
        jobs.update(
            job_id,
            status=JobStatus.FAILED,
            completed_at=datetime.now(timezone.utc).isoformat(),
            error=f"Unexpected error: {exc}",
        )

    # Record job completion metrics (chars, segments, duration, latency, success flag)
    job = jobs.get(job_id)
    if job:
        success = job.status == JobStatus.COMPLETED
        chars = job.chars or 0
        segments = job.segments or 0
        duration_seconds = job.duration_seconds or 0.0
        elapsed_seconds = job.elapsed_seconds or 0.0
        if job.api_key_id:
            metrics.record_job_completed(
                key_id=job.api_key_id,
                chars=chars,
                segments=segments,
                duration_seconds=duration_seconds,
                latency_ms=elapsed_seconds * 1000.0,
                success=success,
            )

    # Fire webhook if set
    job = jobs.get(job_id)
    if job and job.webhook_url:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                await client.post(
                    job.webhook_url,
                    json={"job_id": job_id, "status": job.status.value, "result_url": f"/v1/result/{job_id}"},
                )
        except Exception:
            pass


# --------------------------------------------------------------------------- #
# POST /v1/transcribe
# --------------------------------------------------------------------------- #
@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(
    request: Request,
    file: Optional[UploadFile] = File(default=None),
    url: Optional[str] = Form(default=None),
    language: Optional[str] = Form(default=None),
    model: Optional[str] = Form(default=None),
    word_timestamps: bool = Form(default=False),
    webhook_url: Optional[str] = Form(default=None),
    return_format: str = Form(default="json"),
    normalize: bool = Form(default=True),
) -> TranscribeResponse:
    """
    Submit a transcription job.

    Provide either:
    - `file`: Upload an audio/video file directly (multipart/form-data)
    - `url`: A public URL to download and transcribe

    The job is queued and processed asynchronously.
    Poll GET /v1/status/{job_id} for completion.
    Optionally provide a `webhook_url` to receive a POST notification when done.
    """
    job_id = str(uuid.uuid4())  # Full UUID — prevents enumeration attacks
    source_path: Optional[str] = None
    media_url: Optional[str] = None

    # Enforce max file size
    MAX_BYTES = int(os.environ.get("MAX_UPLOAD_SIZE_MB", 500)) * 1024 * 1024
    if file:
        if file.size and file.size > MAX_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {os.environ.get('MAX_UPLOAD_SIZE_MB', 500)}MB."
            )

    if not file and not url:
        raise HTTPException(status_code=400, detail="Provide either a file or a URL")

    if file:
        if not any(file.filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        upload_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
        with open(upload_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        source_path = str(upload_path)

    elif url:
        # SSRF check
        if not is_url_safe(url):
            raise HTTPException(
                status_code=400,
                detail="URL points to a private or blocked network address."
            )
        media_url = url
        try:
            async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
            ext = Path(url).suffix or ".mp4"
            download_path = UPLOAD_DIR / f"{job_id}_url{ext}"
            with open(download_path, "wb") as f:
                f.write(response.content)
            source_path = str(download_path)
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=400, detail=f"Failed to download URL: {exc}")

    model = model or DEFAULT_MODEL

    # Extract API key identity from authenticated request for metrics tracking
    api_key_id: Optional[str] = None
    try:
        api_key_obj = request.state.api_key_obj
        if api_key_obj:
            api_key_id = api_key_obj.key_id
    except Exception:
        pass

    # Record the API request in metrics (rate-limit counters live in api_keys.verify middleware;
    # metrics tracks usage depth: chars, segments, duration, latency)
    if api_key_id:
        metrics.record_request(api_key_id)

    job = jobs.create(
        job_id=job_id,
        source_url=media_url,
        source_path=source_path,
        language=language,
        model=model,
        word_timestamps=word_timestamps,
        webhook_url=webhook_url,
        return_format=return_format,
        api_key_id=api_key_id,
    )

    if jobs.count_active() < MAX_CONCURRENT_JOBS:
        asyncio.create_task(_run_transcription_job(job_id))

    return TranscribeResponse(
        job_id=job_id,
        status=JobStatus.QUEUED,
        created_at=job.created_at,
        message=f"Job queued. Poll GET /v1/status/{job_id} or use webhook: {webhook_url or '(none)'}"
    )




# --------------------------------------------------------------------------- #
# POST /v1/transcribe/sync — synchronous one-call transcription
# --------------------------------------------------------------------------- #
@router.post("/transcribe/sync", response_model=ResultResponse)
async def transcribe_sync(
    request: Request,
    file: Optional[UploadFile] = File(default=None),
    url: Optional[str] = Form(default=None),
    language: Optional[str] = Form(default=None),
    model: Optional[str] = Form(default=None),
    word_timestamps: bool = Form(default=False),
    webhook_url: Optional[str] = Form(default=None),
    return_format: str = Form(default="json"),
    normalize: bool = Form(default=True),
    timeout_seconds: int = Form(default=300),
) -> ResultResponse:
    """
    One-call synchronous transcription.

    Submits the job and blocks until the transcript is complete
    (or until the timeout is reached).

    Provide either:
    - `file`: Upload an audio/video file directly (multipart/form-data)
    - `url`: A public URL to download and transcribe

    Returns the full structured transcript directly when ready.
    Use this for files under ~30 minutes; longer files use async /v1/transcribe.

    Timeout: defaults to 300 seconds (5 minutes). Pass `timeout_seconds` to adjust.
    """
    job_id = str(uuid.uuid4())  # Full UUID — prevents enumeration attacks
    source_path: Optional[str] = None
    media_url: Optional[str] = None

    # Enforce max file size
    MAX_BYTES = int(os.environ.get("MAX_UPLOAD_SIZE_MB", 500)) * 1024 * 1024
    if file:
        if file.size and file.size > MAX_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {os.environ.get('MAX_UPLOAD_SIZE_MB', 500)}MB."
            )

    if not file and not url:
        raise HTTPException(status_code=400, detail="Provide either a file or a URL")

    if file:
        if not any(file.filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        upload_path = UPLOAD_DIR / f"{job_id}_{file.filename}"
        with open(upload_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        source_path = str(upload_path)

    elif url:
        # SSRF check
        if not is_url_safe(url):
            raise HTTPException(
                status_code=400,
                detail="URL points to a private or blocked network address."
            )
        media_url = url
        try:
            async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
            ext = Path(url).suffix or ".mp4"
            download_path = UPLOAD_DIR / f"{job_id}_url{ext}"
            with open(download_path, "wb") as f:
                f.write(response.content)
            source_path = str(download_path)
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=400, detail=f"Failed to download URL: {exc}")

    model = model or DEFAULT_MODEL

    # Extract API key identity from authenticated request for metrics tracking
    api_key_id: Optional[str] = None
    try:
        api_key_obj = request.state.api_key_obj
        if api_key_obj:
            api_key_id = api_key_obj.key_id
    except Exception:
        pass

    # Record the API request in metrics
    if api_key_id:
        metrics.record_request(api_key_id)

    job = jobs.create(
        job_id=job_id,
        source_url=media_url,
        source_path=source_path,
        language=language,
        model=model,
        word_timestamps=word_timestamps,
        webhook_url=webhook_url,
        return_format=return_format,
        api_key_id=api_key_id,
    )

    if jobs.count_active() < MAX_CONCURRENT_JOBS:
        asyncio.create_task(_run_transcription_job(job_id))

    # Poll for completion
    poll_interval = 2.0  # seconds
    max_interval = 10.0
    elapsed = 0.0

    while elapsed < timeout_seconds:
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
        poll_interval = min(poll_interval * 1.5, max_interval)

        current_job = jobs.get(job_id)
        if not current_job:
            raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
        if current_job.status == JobStatus.COMPLETED:
            return _job_to_result_response(current_job)
        if current_job.status == JobStatus.FAILED:
            raise HTTPException(
                status_code=422,
                detail=f"Transcription failed: {current_job.error or 'unknown error'}",
            )

    # Timed out
    raise HTTPException(
        status_code=408,
        detail=f"Transcription timed out after {timeout_seconds} seconds. "
               f"Job {job_id} is still {jobs.get(job_id).status.value if jobs.get(job_id) else 'unknown'}. "
               f"Use GET /v1/status/{job_id} to check status.",
    )


# --------------------------------------------------------------------------- #
# GET /v1/limits — Rate limit status for the authenticated key
# --------------------------------------------------------------------------- #
@router.get("/limits", response_model=LimitsResponse)
async def get_limits(request: Request) -> LimitsResponse:
    """
    Return current rate limit status for the authenticated API key.

    Shows daily and per-minute usage vs limits, plus reset timestamps.
    Use this to check quota before submitting large batches.
    """
    from webhooks.api_keys import api_keys

    api_key_id: Optional[str] = None
    try:
        api_key_obj = request.state.api_key_obj
        if api_key_obj:
            api_key_id = api_key_obj.key_id
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication required")

    if not api_key_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    usage = api_keys.usage(api_key_id)
    if not usage:
        raise HTTPException(status_code=404, detail="API key not found")

    return LimitsResponse(**usage)

# --------------------------------------------------------------------------- #
# GET /v1/status/{job_id}
# --------------------------------------------------------------------------- #
@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str) -> StatusResponse:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    return _job_to_status_response(job)


# --------------------------------------------------------------------------- #
# GET /v1/result/{job_id}
# --------------------------------------------------------------------------- #
@router.get("/result/{job_id}", response_model=ResultResponse)
async def get_result(job_id: str) -> ResultResponse:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    if job.status == JobStatus.QUEUED:
        raise HTTPException(status_code=202, detail=f"Job {job_id} is still queued")
    if job.status == JobStatus.PROCESSING:
        raise HTTPException(status_code=202, detail=f"Job {job_id} is still processing")
    return _job_to_result_response(job)


# --------------------------------------------------------------------------- #
# GET /v1/jobs
# --------------------------------------------------------------------------- #
@router.get("/jobs")
async def list_jobs(
    limit: int = Query(default=50, ge=1, le=500),
    status_filter: Optional[str] = Query(default=None),
) -> dict:
    all_jobs = jobs.all()
    filtered = []
    for j in all_jobs.values():
        if status_filter is None or j.status.value == status_filter:
            filtered.append(j.to_status_dict())
    filtered.sort(key=lambda x: x["created_at"], reverse=True)
    return {
        "jobs": filtered[:limit],
        "total": len(filtered),
        "active": jobs.count_active(),
        "max_concurrent": MAX_CONCURRENT_JOBS,
    }


# --------------------------------------------------------------------------- #
# DELETE /v1/job/{job_id}
# --------------------------------------------------------------------------- #
@router.delete("/job/{job_id}")
async def delete_job(job_id: str) -> dict:
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    if job.source_path and Path(job.source_path).exists():
        try:
            Path(job.source_path).unlink()
        except OSError:
            pass
    if job.transcript_json_path and Path(job.transcript_json_path).exists():
        try:
            Path(job.transcript_json_path).unlink()
        except OSError:
            pass
    del jobs.all()[job_id]
    return {"ok": True, "job_id": job_id}


# --------------------------------------------------------------------------- #
# GET /v1/download/{job_id}
# --------------------------------------------------------------------------- #
@router.get("/download/{job_id}")
async def download_result(
    job_id: str,
    format: str = Query(default="json"),
):
    """Download the transcript result in the specified format."""
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job not found: {job_id}")
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Job not completed: {job.status}")

    if job.transcript_json_path and Path(job.transcript_json_path).exists():
        if format == "json":
            return FileResponse(
                job.transcript_json_path,
                media_type="application/json",
                filename=f"{job_id}.transcript.json",
            )
        with open(job.transcript_json_path) as f:
            data = json.load(f)

        if format == "txt":
            content = data.get("text", data.get("normalized_text", ""))
            return PlainTextResponse(content, media_type="text/plain", filename=f"{job_id}.txt")

        if format == "srt":
            segments = data.get("segments", [])
            lines = []
            for idx, seg in enumerate(segments, 1):
                lines.extend([
                    str(idx),
                    f"{seg.get('start_time', '00:00:00')} --> {seg.get('end_time', '00:00:00')}",
                    seg.get("text", "").strip(),
                    "",
                ])
            content = "\n".join(lines).strip() + "\n"
            return PlainTextResponse(content, media_type="text/plain", filename=f"{job_id}.srt")

        if format == "vtt":
            segments = data.get("segments", [])
            lines = ["WEBVTT", ""]
            for seg in segments:
                start = seg.get("start_time", "00:00:00").replace(",", ".")
                end = seg.get("end_time", "00:00:00").replace(",", ".")
                lines.extend([f"{start} --> {end}", seg.get("text", "").strip(), ""])
            content = "\n".join(lines).strip() + "\n"
            return PlainTextResponse(content, media_type="text/vtt", filename=f"{job_id}.vtt")

    raise HTTPException(status_code=404, detail="Transcript file not found")
