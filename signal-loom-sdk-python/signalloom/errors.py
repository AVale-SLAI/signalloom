"""Error classes for Signal Loom SDK."""

from __future__ import annotations


class SignalLoomError(Exception):
    """Base exception for all Signal Loom errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r}, status_code={self.status_code!r})"


class InvalidRequestError(SignalLoomError):
    """Raised for 400 Bad Request responses."""

    pass


class RateLimitError(SignalLoomError):
    """Raised for 429 Too Many Requests responses."""

    pass


class JobFailedError(SignalLoomError):
    """Raised when a job completed but encountered a failure."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        job_id: str | None = None,
    ):
        super().__init__(message, status_code)
        self.job_id = job_id


class TimeoutError(SignalLoomError):
    """Raised when synchronous transcription exceeds the timeout."""

    def __init__(self, message: str, timeout: int | None = None):
        super().__init__(message)
        self.timeout = timeout
