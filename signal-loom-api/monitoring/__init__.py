# Signal Loom AI — Monitoring and Metrics
"""
Lightweight metrics and usage tracking for Signal Loom API.

Tracks:
- Requests per day/week/month
- Minutes of audio processed
- Error rates
- Latency percentiles
- Active API keys
- Webhook delivery success rates

In-memory for MVP. Swap for Redis/InfluxDB + Grafana in production.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional

# --------------------------------------------------------------------------- #
# Data structures
# --------------------------------------------------------------------------- #
@dataclass
class ApiKeyStats:
    key_id: str  # truncated key for display
    created_at: str
    total_requests: int = 0
    total_chars: int = 0
    total_segments: int = 0
    total_duration_seconds: float = 0.0
    total_jobs: int = 0
    successful_jobs: int = 0
    failed_jobs: int = 0
    last_seen: str = ""


@dataclass
class DailyStats:
    date: str  # YYYY-MM-DD
    total_requests: int = 0
    total_chars: int = 0
    total_duration_seconds: float = 0.0
    total_jobs: int = 0
    successful_jobs: int = 0
    failed_jobs: int = 0
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    webhook_success: int = 0
    webhook_failed: int = 0


# --------------------------------------------------------------------------- #
# In-memory metrics store
# --------------------------------------------------------------------------- #
class Metrics:
    """
    Thread-safe in-memory metrics store.

    Records:
    - Per-key usage stats
    - Daily aggregate stats
    - Latency histograms
    - Webhook delivery stats
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._key_stats: Dict[str, ApiKeyStats] = {}
        self._daily: Dict[str, DailyStats] = {}
        self._latencies_ms: Dict[str, List[float]] = defaultdict(list)  # keyed by date
        self._webhook_success: int = 0
        self._webhook_failed: int = 0
        self._start_time = time.time()

    def _today(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _ensure_daily(self, date: str) -> None:
        if date not in self._daily:
            self._daily[date] = DailyStats(date=date)

    # --------------------------------------------------------------------------- #
    # Recording
    # --------------------------------------------------------------------------- #
    def record_request(self, key_id: str) -> None:
        with self._lock:
            today = self._today()
            self._ensure_daily(today)
            self._daily[today].total_requests += 1
            if key_id not in self._key_stats:
                self._key_stats[key_id] = ApiKeyStats(
                    key_id=key_id,
                    created_at=datetime.now(timezone.utc).isoformat(),
                )
            ks = self._key_stats[key_id]
            ks.total_requests += 1
            ks.last_seen = datetime.now(timezone.utc).isoformat()

    def record_job_completed(
        self,
        key_id: str,
        chars: int,
        segments: int,
        duration_seconds: float,
        latency_ms: float,
        success: bool,
    ) -> None:
        with self._lock:
            today = self._today()
            self._ensure_daily(today)
            d = self._daily[today]

            d.total_jobs += 1
            if success:
                d.successful_jobs += 1
            else:
                d.failed_jobs += 1

            d.total_chars += chars
            d.total_duration_seconds += duration_seconds

            # Latency tracking (keep last 1000 per day)
            self._latencies_ms[today].append(latency_ms)
            if len(self._latencies_ms[today]) > 1000:
                self._latencies_ms[today] = self._latencies_ms[today][-1000:]

            if self._latencies_ms[today]:
                sorted_lat = sorted(self._latencies_ms[today])
                n = len(sorted_lat)
                d.avg_latency_ms = sum(sorted_lat) / n
                d.p95_latency_ms = sorted_lat[int(n * 0.95)]
                d.p99_latency_ms = sorted_lat[int(n * 0.99)]

            if key_id in self._key_stats:
                ks = self._key_stats[key_id]
                ks.total_chars += chars
                ks.total_segments += segments
                ks.total_duration_seconds += duration_seconds
                ks.total_jobs += 1
                if success:
                    ks.successful_jobs += 1
                else:
                    ks.failed_jobs += 1

    def record_webhook(self, success: bool) -> None:
        with self._lock:
            today = self._today()
            self._ensure_daily(today)
            if success:
                self._webhook_success += 1
                self._daily[today].webhook_success += 1
            else:
                self._webhook_failed += 1
                self._daily[today].webhook_failed += 1

    # --------------------------------------------------------------------------- #
    # Reading
    # --------------------------------------------------------------------------- #
    def get_key_stats(self, key_id: str) -> Optional[ApiKeyStats]:
        with self._lock:
            return self._key_stats.get(key_id)

    def get_all_key_stats(self) -> List[ApiKeyStats]:
        with self._lock:
            return list(self._key_stats.values())

    def get_daily_stats(self, date: str) -> Optional[DailyStats]:
        with self._lock:
            return self._daily.get(date)

    def get_recent_daily_stats(self, days: int = 7) -> List[DailyStats]:
        with self._lock:
            today = datetime.now(timezone.utc)
            result = []
            for i in range(days):
                d = (today.replace(hour=0, minute=0, second=0, microsecond=0) -
                     datetime.timedelta(days=i)).strftime("%Y-%m-%d")
                if d in self._daily:
                    result.append(self._daily[d])
            return result

    def get_summary(self) -> dict:
        with self._lock:
            today = self._today()
            self._ensure_daily(today)
            d = self._daily[today]
            active_keys = len(self._key_stats)
            uptime_seconds = time.time() - self._start_time

            # Total across all time
            total_requests = sum(x.total_requests for x in self._key_stats.values())
            total_chars = sum(x.total_chars for x in self._key_stats.values())
            total_duration = sum(x.total_duration_seconds for x in self._key_stats.values())
            total_jobs = sum(x.total_jobs for x in self._key_stats.values())
            successful = sum(x.successful_jobs for x in self._key_stats.values())
            failed = sum(x.failed_jobs for x in self._key_stats.values())

            return {
                "uptime_seconds": round(uptime_seconds, 1),
                "active_api_keys": active_keys,
                "today": {
                    "requests": d.total_requests,
                    "jobs": d.total_jobs,
                    "chars": d.total_chars,
                    "duration_seconds": round(d.total_duration_seconds, 1),
                    "successful": d.successful_jobs,
                    "failed": d.failed_jobs,
                    "avg_latency_ms": round(d.avg_latency_ms, 1),
                    "p95_latency_ms": round(d.p95_latency_ms, 1),
                    "p99_latency_ms": round(d.p99_latency_ms, 1),
                },
                "totals": {
                    "requests": total_requests,
                    "chars": total_chars,
                    "duration_seconds": round(total_duration, 1),
                    "jobs": total_jobs,
                    "successful": successful,
                    "failed": failed,
                },
                "webhooks": {
                    "success": self._webhook_success,
                    "failed": self._webhook_failed,
                    "rate": round(self._webhook_success / max(1, self._webhook_success + self._webhook_failed), 3),
                },
                "active_keys": [
                    {
                        "key_id": ks.key_id,
                        "requests": ks.total_requests,
                        "jobs": ks.total_jobs,
                        "chars": ks.total_chars,
                        "last_seen": ks.last_seen,
                    }
                    for ks in self._key_stats.values()
                ],
            }


# Singleton
metrics = Metrics()
