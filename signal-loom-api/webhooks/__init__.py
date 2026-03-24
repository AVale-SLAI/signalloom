# Signal Loom AI — Webhook Manager
"""
Webhook delivery with retry logic and delivery tracking.

Features:
- Configurable retry with exponential backoff
- Delivery status tracking (pending, delivered, failed)
- Per-webhook delivery log
- Webhook signature verification (HMAC-SHA256)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
class DeliveryStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class WebhookDelivery:
    webhook_id: str
    url: str
    payload: Dict[str, Any]
    status: DeliveryStatus = DeliveryStatus.PENDING
    attempts: int = 0
    max_attempts: int = 3
    next_retry: Optional[str] = None
    last_attempt: Optional[str] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    delivered_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "webhook_id": self.webhook_id,
            "url": self.url,
            "status": self.status.value,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "next_retry": self.next_retry,
            "last_attempt": self.last_attempt,
            "response_status": self.response_status,
            "response_body": self.response_body[:200] if self.response_body else None,
            "created_at": self.created_at,
            "delivered_at": self.delivered_at,
        }


# --------------------------------------------------------------------------- #
# WebhookManager
# --------------------------------------------------------------------------- #
class WebhookManager:
    """
    Manages webhook delivery with:
    - Exponential backoff retries
    - Configurable max attempts
    - Delivery status tracking
    - HMAC signature generation for verification
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 30.0,
        max_delay: float = 3600.0,
    ) -> None:
        self._lock = threading.RLock()
        self._deliveries: Dict[str, WebhookDelivery] = {}
        self._deliveries_by_job: Dict[str, List[str]] = {}  # job_id -> webhook_ids
        self._max_attempts = max_attempts
        self._base_delay = base_delay
        self._max_delay = max_delay

    def _compute_delay(self, attempt: int) -> float:
        """Exponential backoff with jitter cap."""
        delay = self._base_delay * (2 ** (attempt - 1))
        import random
        jitter = delay * 0.1 * random.random()
        return min(delay + jitter, self._max_delay)

    def _generate_signature(self, payload: str, secret: str) -> str:
        """HMAC-SHA256 signature for webhook verification."""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256,
        ).hexdigest()

    def _deliver(self, delivery: WebhookDelivery, secret: Optional[str] = None) -> bool:
        """Attempt to deliver a webhook."""
        delivery.attempts += 1
        delivery.last_attempt = datetime.now(timezone.utc).isoformat()

        try:
            headers = {"Content-Type": "application/json"}
            if secret:
                payload_str = json.dumps(delivery.payload)
                signature = self._generate_signature(payload_str, secret)
                headers["X-SignalLoom-Signature"] = signature
                headers["X-SignalLoom-Timestamp"] = str(int(time.time()))

            with httpx.Client(timeout=30) as client:
                response = client.post(
                    delivery.url,
                    json=delivery.payload,
                    headers=headers,
                )
                delivery.response_status = response.status_code
                delivery.response_body = response.text[:500]

            if 200 <= delivery.response_status < 300:
                delivery.status = DeliveryStatus.DELIVERED
                delivery.delivered_at = datetime.now(timezone.utc).isoformat()
                return True
            else:
                delivery.status = DeliveryStatus.RETRYING
                delivery.next_retry = datetime.fromtimestamp(
                    time.time() + self._compute_delay(delivery.attempts),
                    tz=timezone.utc,
                ).isoformat()
                return False

        except httpx.Timeout:
            delivery.status = DeliveryStatus.RETRYING
            delivery.response_status = None
            delivery.response_body = "Connection timeout"
            delivery.next_retry = datetime.fromtimestamp(
                time.time() + self._compute_delay(delivery.attempts),
                tz=timezone.utc,
            ).isoformat()
            return False

        except Exception as exc:
            delivery.status = DeliveryStatus.RETRYING
            delivery.response_status = None
            delivery.response_body = str(exc)[:200]
            delivery.next_retry = datetime.fromtimestamp(
                time.time() + self._compute_delay(delivery.attempts),
                tz=timezone.utc,
            ).isoformat()
            return False

    def enqueue(
        self,
        url: str,
        payload: Dict[str, Any],
        job_id: Optional[str] = None,
        max_attempts: Optional[int] = None,
    ) -> str:
        """Enqueue a webhook for delivery."""
        webhook_id = str(uuid.uuid4())[:8]
        delivery = WebhookDelivery(
            webhook_id=webhook_id,
            url=url,
            payload=payload,
            max_attempts=max_attempts or self._max_attempts,
        )
        with self._lock:
            self._deliveries[webhook_id] = delivery
            if job_id:
                if job_id not in self._deliveries_by_job:
                    self._deliveries_by_job[job_id] = []
                self._deliveries_by_job[job_id].append(webhook_id)

        # Deliver synchronously in background thread
        def _deliver_in_thread():
            d = self._deliveries[webhook_id]
            while d.attempts < d.max_attempts and d.status != DeliveryStatus.DELIVERED:
                success = self._deliver(d)
                if success:
                    break
                if d.status == DeliveryStatus.RETRYING:
                    delay = self._compute_delay(d.attempts)
                    time.sleep(min(delay, 60))  # cap at 60s for demo purposes

            if d.status != DeliveryStatus.DELIVERED:
                d.status = DeliveryStatus.FAILED

        t = threading.Thread(target=_deliver_in_thread, daemon=True)
        t.start()
        return webhook_id

    def get(self, webhook_id: str) -> Optional[WebhookDelivery]:
        with self._lock:
            return self._deliveries.get(webhook_id)

    def get_by_job(self, job_id: str) -> List[WebhookDelivery]:
        with self._lock:
            ids = self._deliveries_by_job.get(job_id, [])
            return [self._deliveries[w] for w in ids if w in self._deliveries]

    def get_all(self) -> List[WebhookDelivery]:
        with self._lock:
            return list(self._deliveries.values())

    def get_pending_retry(self) -> List[WebhookDelivery]:
        """Get webhooks that are due for retry."""
        with self._lock:
            now = datetime.now(timezone.utc)
            pending = []
            for d in self._deliveries.values():
                if d.status == DeliveryStatus.RETRYING and d.next_retry:
                    if datetime.fromisoformat(d.next_retry) <= now:
                        pending.append(d)
            return pending


# Singleton
webhooks = WebhookManager()
