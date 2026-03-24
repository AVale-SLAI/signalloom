"""Utility helpers for Signal Loom SDK."""

from __future__ import annotations

import random
import time
from typing import BinaryIO, Callable, TypeVar

T = TypeVar("T")


def exponential_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    jitter: bool = True,
) -> float:
    """Return seconds to wait before next retry with exponential backoff.

    Args:
        attempt: Zero-based retry attempt number.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay cap in seconds.
        jitter: Add random jitter to spread out retries.
    """
    delay = min(base_delay * (2**attempt), max_delay)
    if jitter:
        delay *= random.uniform(0.5, 1.5)
    return delay


def poll_until_done(
    get_status: Callable[[], str],
    timeout: int = 300,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    terminal_statuses: tuple[str, ...] = ("completed", "failed", "cancelled"),
) -> str:
    """Poll a status endpoint until a terminal status is reached.

    Args:
        get_status: Callable that returns current status string.
        timeout: Maximum seconds to wait before raising TimeoutError.
        base_delay: Initial polling interval in seconds.
        max_delay: Maximum polling interval in seconds.
        terminal_statuses: Statuses considered terminal (stop polling).

    Returns:
        Final status string.

    Raises:
        TimeoutError: If polling exceeds the specified timeout.
    """
    start = time.monotonic()
    attempt = 0

    while True:
        status = get_status()
        if status in terminal_statuses:
            return status

        elapsed = time.monotonic() - start
        remaining = timeout - elapsed
        if remaining <= 0:
            raise TimeoutError(
                f"Polling timed out after {timeout}s (last status: {status!r})",
                timeout=timeout,
            )

        delay = exponential_backoff(attempt, base_delay, max_delay)
        delay = min(delay, remaining)  # don't wait past the timeout
        time.sleep(delay)
        attempt += 1


def guess_content_type(filename: str) -> str:
    """Guess MIME type from a filename extension."""
    import mimetypes

    mime, _ = mimetypes.guess_type(filename)
    return mime or "application/octet-stream"


def filename_from_path(path: str) -> str:
    """Extract the basename from a file path."""
    import os

    return os.path.basename(path)
