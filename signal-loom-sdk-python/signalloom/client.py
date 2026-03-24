"""Signal Loom client implementation."""

from __future__ import annotations

import os
import time
from io import IOBase
from typing import BinaryIO, List, Optional, Union

import httpx

from signalloom.errors import (
    InvalidRequestError,
    JobFailedError,
    RateLimitError,
    SignalLoomError,
    TimeoutError,
)
from signalloom.models import (
    Job,
    JobStatus,
    ReturnFormat,
    ServerInfo,
    Transcript,
    TranscriptMetadata,
    TranscriptSegment,
)
from signalloom.utils import exponential_backoff, guess_content_type, filename_from_path

# Re-export TimeoutError so callers can catch it directly
__all__ = ["TimeoutError"]


BinaryData = Union[BinaryIO, bytes, IOBase, str]


class SignalLoom:
    """Python SDK client for the Signal Loom AI API.

    Parameters
    ----------
    api_key : str, optional
        API key for authentication. Falls back to the ``SIGNAL_LOOM_API_KEY``
        environment variable.
    base_url : str, optional
        Base URL of the Signal Loom API. Falls back to the
        ``SIGNAL_LOOM_BASE_URL`` environment variable, then
        ``http://localhost:18790``.
    timeout : int, default 300
        Default timeout in seconds for synchronous transcription calls.
    """

    DEFAULT_BASE_URL = "http://localhost:18790"
    DEFAULT_TIMEOUT = 300

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        self._api_key = api_key or os.environ.get("SIGNAL_LOOM_API_KEY")
        self._base_url = base_url or os.environ.get(
            "SIGNAL_LOOM_BASE_URL", self.DEFAULT_BASE_URL
        ).rstrip("/")
        self._timeout = timeout
        self._client: httpx.Client | None = None

    # ── HTTP client (lazy) ─────────────────────────────────────────────────────

    @property
    def _http(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(
                base_url=self._base_url,
                timeout=httpx.Timeout(self._timeout),
                headers=self._build_headers(),
            )
        return self._client

    def _build_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "User-Agent": f"signal-loom-python-sdk/0.1.0",
            "Accept": "application/json",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    def _close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    def __enter__(self) -> "SignalLoom":
        return self

    def __exit__(self, *args) -> None:
        self._close()

    # ── Internal request helpers ──────────────────────────────────────────────

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        data: dict | None = None,
        files: dict | None = None,
        headers: dict | None = None,
        raise_on_status: bool = True,
    ) -> httpx.Response:
        """Make an HTTP request and handle common error cases."""
        url = f"{self._base_url}{path}"
        try:
            response = self._http.request(
                method=method,
                url=path,  # httpx uses path when base_url is set
                params=params,
                data=data,
                files=files,
                headers=headers,
            )
        except httpx.TimeoutException as exc:
            raise TimeoutError(
                f"Request to {method} {path} timed out",
                timeout=self._timeout,
            ) from exc
        except httpx.HTTPError as exc:
            raise SignalLoomError(f"HTTP error: {exc}") from exc

        if raise_on_status:
            self._raise_for_status(response)
        return response

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Map HTTP status codes to SDK exceptions."""
        if response.is_success:
            return
        status = response.status_code
        text = response.text

        if status == 400:
            raise InvalidRequestError(text, status_code=status)
        if status == 429:
            raise RateLimitError(text, status_code=status)
        raise SignalLoomError(text, status_code=status)

    # ── Public API ─────────────────────────────────────────────────────────────

    @property
    def health(self) -> dict:
        """Return server health information.

        Returns
        -------
        dict
            The raw JSON health response.
        """
        resp = self._request("GET", "/health", raise_on_status=False)
        return resp.json()

    @property
    def info(self) -> ServerInfo:
        """Return server capabilities and available models.

        Returns
        -------
        ServerInfo
        """
        resp = self._request("GET", "/v1/info")
        return ServerInfo(**resp.json())

    @property
    def models(self) -> List[str]:
        """Return list of available transcription models."""
        return self.info.models or []

    # ── Transcription ──────────────────────────────────────────────────────────

    def transcribe(
        self,
        file: BinaryData | None = None,
        url: str | None = None,
        *,
        model: str = "mlx-community/whisper-large-v3-turbo",
        language: str | None = None,
        webhook_url: str | None = None,
        return_format: ReturnFormat = ReturnFormat.JSON,
        word_timestamps: bool = False,
    ) -> Job:
        """Submit an asynchronous transcription job.

        Exactly one of ``file`` or ``url`` must be provided.

        Parameters
        ----------
        file : BinaryData, optional
            Local audio/video file to upload. Can be a file handle, bytes,
            or a path string.
        url : str, optional
            Remote URL to an audio/video file.
        model : str, optional
            Model ID to use for transcription.
            Default: ``mlx-community/whisper-large-v3-turbo``.
        language : str, optional
            BCP-47 language code (e.g. ``"en"``, ``"es"``). If omitted, the
            language is auto-detected.
        webhook_url : str, optional
            URL to receive a POST request when the job completes.
        return_format : ReturnFormat, optional
            Desired output format. Default: ``ReturnFormat.JSON``.
        word_timestamps : bool, optional
            Whether to include word-level timestamps. Default: ``False``.

        Returns
        -------
        Job
            A job object with a ``job_id`` that can be used with
            :meth:`get_job` or :meth:`get_result`.

        Raises
        ------
        InvalidRequestError
            If neither or both of ``file`` and ``url`` are provided.
        """
        if (file is None and url is None) or (file is not None and url is not None):
            raise InvalidRequestError(
                "Exactly one of 'file' or 'url' must be provided",
                status_code=400,
            )

        data: dict[str, Any] = {
            "model": model,
            "return_format": return_format.value,
            "word_timestamps": "true" if word_timestamps else "false",
        }
        if language:
            data["language"] = language
        if webhook_url:
            data["webhook_url"] = webhook_url

        files: dict[str, Any] | None = None
        _opened_file = None  # track file handle we opened so we can close it after
        if file is not None:
            if isinstance(file, str):
                # Treat as a file path
                path = file
                name = filename_from_path(path)
                content_type = guess_content_type(path)
                _opened_file = open(path, "rb")
                file_handle = _opened_file
            elif isinstance(file, bytes):
                name = "upload"
                content_type = "application/octet-stream"
                file_handle = file
            else:
                name = getattr(file, "name", "upload")
                content_type = guess_content_type(name)
                file_handle = file

            files = {
                "file": (name, file_handle, content_type)  # type: ignore[arg-type]
            }

        try:
            resp = self._request(
                "POST",
                "/v1/transcribe",
                data=data,
                files=files,
                raise_on_status=False,
            )
        finally:
            # Close any file handles we opened
            if _opened_file is not None:
                _opened_file.close()

        self._raise_for_status(resp)
        return Job(**resp.json())

    def transcribe_sync(
        self,
        file: BinaryData | None = None,
        url: str | None = None,
        *,
        timeout: int | None = None,
        model: str = "mlx-community/whisper-large-v3-turbo",
        language: str | None = None,
        webhook_url: str | None = None,
        return_format: ReturnFormat = ReturnFormat.JSON,
        word_timestamps: bool = False,
    ) -> Transcript:
        """Synchronous one-call transcription.

        Blocks until the transcription job completes or the timeout is
        reached. Internally polls the job status endpoint with exponential
        back-off.

        Parameters
        ----------
        file : BinaryData, optional
            Local audio/video file to upload.
        url : str, optional
            Remote URL to an audio/video file.
        timeout : int, optional
            Maximum seconds to wait. Defaults to the ``timeout`` passed to
            the constructor.
        model : str, optional
            Model ID. Default: ``mlx-community/whisper-large-v3-turbo``.
        language : str, optional
            BCP-47 language code.
        webhook_url : str, optional
            Webhook URL for completion notification.
        return_format : ReturnFormat, optional
            Output format. Default: ``ReturnFormat.JSON``.
        word_timestamps : bool, optional
            Include word-level timestamps. Default: ``False``.

        Returns
        -------
        Transcript
            The completed transcription result.

        Raises
        ------
        TimeoutError
            If the job does not complete within ``timeout`` seconds.
        JobFailedError
            If the job completed with a failure.
        """
        effective_timeout = timeout if timeout is not None else self._timeout

        job = self.transcribe(
            file=file,
            url=url,
            model=model,
            language=language,
            webhook_url=webhook_url,
            return_format=return_format,
            word_timestamps=word_timestamps,
        )

        start = time.monotonic()

        def get_status() -> str:
            elapsed = time.monotonic() - start
            remaining = effective_timeout - elapsed
            if remaining <= 0:
                return "timeout"
            j = self.get_job(job.job_id)
            return j.status if isinstance(j.status, str) else j.status.value  # type: ignore[union-attr]

        attempt = 0
        while True:
            elapsed = time.monotonic() - start
            remaining = effective_timeout - elapsed
            if remaining <= 0:
                raise TimeoutError(
                    f"Transcription timed out after {effective_timeout}s",
                    timeout=effective_timeout,
                )

            j = self.get_job(job.job_id)
            status = j.status.value if hasattr(j.status, "value") else j.status  # type: ignore[union-attr]

            if status == "completed":
                result = self.get_result(job.job_id)
                if result.status == JobStatus.FAILED:
                    raise JobFailedError(
                        "Transcription job failed",
                        job_id=job.job_id,
                    )
                return result

            if status in ("failed", "cancelled"):
                raise JobFailedError(
                    f"Transcription job {status}: {j.error}",
                    job_id=job.job_id,
                )

            # Wait before next poll
            delay = exponential_backoff(attempt, base_delay=1.0, max_delay=30.0)
            delay = min(delay, remaining)
            time.sleep(delay)
            attempt += 1

    def get_job(self, job_id: str) -> Job:
        """Fetch the current status of a transcription job.

        Parameters
        ----------
        job_id : str
            The job identifier returned by :meth:`transcribe`.

        Returns
        -------
        Job
        """
        resp = self._request("GET", f"/v1/status/{job_id}")
        return Job(**resp.json())

    def get_result(self, job_id: str) -> Transcript:
        """Fetch the completed transcription result.

        Parameters
        ----------
        job_id : str

        Returns
        -------
        Transcript

        Raises
        ------
        JobFailedError
            If the job has failed.
        """
        resp = self._request(
            "GET",
            f"/v1/result/{job_id}",
            raise_on_status=False,
        )
        self._raise_for_status(resp)
        data = resp.json()
        status = data.get("status", "")
        if status == "failed" or (isinstance(status, str) and "fail" in status.lower()):
            raise JobFailedError(
                f"Job {job_id} failed",
                job_id=job_id,
            )
        # Flatten the nested transcript object into top-level fields
        # so Transcript(**flat_data) receives language, duration_seconds, etc.
        flat = dict(data)
        nested = flat.pop("transcript", None)
        if nested and isinstance(nested, dict):
            # Remap API field names → SDK model field names
            SEGMENT_RENAME = {
                "segment_id": "id",
                "start_seconds": "start",
                "end_seconds": "end",
            }
            for k, v in nested.items():
                if k not in flat:
                    if k == "segments" and isinstance(v, list):
                        # Remap each segment's field names
                        flat_segments = []
                        for seg in v:
                            if isinstance(seg, dict):
                                renamed_seg = {}
                                for sk, sv in seg.items():
                                    renamed_seg[SEGMENT_RENAME.get(sk, sk)] = sv
                                flat_segments.append(renamed_seg)
                            else:
                                flat_segments.append(seg)
                        flat[k] = flat_segments
                    else:
                        flat[k] = v
        return Transcript(**flat)

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued or running transcription job.

        Parameters
        ----------
        job_id : str

        Returns
        -------
        bool
            ``True`` if the job was successfully cancelled.
        """
        resp = self._request(
            "DELETE",
            f"/v1/job/{job_id}",
            raise_on_status=False,
        )
        if resp.status_code == 404:
            return False
        self._raise_for_status(resp)
        return True

    def list_jobs(
        self,
        status: str | None = None,
    ) -> List[Job]:
        """List transcription jobs, optionally filtered by status.

        Parameters
        ----------
        status : str, optional
            Filter to jobs with this status (e.g. ``"queued"``,
            ``"processing"``, ``"completed"``).

        Returns
        -------
        List[Job]
        """
        params = {"status": status} if status else None
        resp = self._request(
            "GET",
            "/v1/jobs",
            params=params,
            raise_on_status=False,
        )
        if resp.status_code == 404:
            return []
        self._raise_for_status(resp)
        return [Job(**item) for item in resp.json()]
