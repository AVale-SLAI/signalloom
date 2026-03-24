# Signal Loom AI — API Key Management
"""
Simple API key management for Signal Loom API.

Supports:
- Creating new API keys (with optional tier/plan)
- Revoking keys
- Tracking usage per key
- Key metadata (tier, created_at, last_used)
- Simple rate limiting per key

In-memory for MVP. Swap for Postgres in production.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


# --------------------------------------------------------------------------- #
# Types
# --------------------------------------------------------------------------- #
class KeyTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    SCALE = "scale"
    ENTERPRISE = "enterprise"


TIER_LIMITS = {
    KeyTier.FREE: {
        "requests_per_day": 100,
        "requests_per_minute": 10,
        "audio_minutes_per_month": 100,
    },
    KeyTier.STARTER: {
        "requests_per_day": 1000,
        "requests_per_minute": 50,
        "audio_minutes_per_month": 10_000,
    },
    KeyTier.PRO: {
        "requests_per_day": 10_000,
        "requests_per_minute": 200,
        "audio_minutes_per_month": 100_000,
    },
    KeyTier.SCALE: {
        "requests_per_day": 100_000,
        "requests_per_minute": 1000,
        "audio_minutes_per_month": 1_000_000,
    },
    KeyTier.ENTERPRISE: {
        "requests_per_day": -1,  # unlimited
        "requests_per_minute": -1,
        "audio_minutes_per_month": -1,
    },
}

TIERS = TIER_LIMITS  # Alias used by admin router


# --------------------------------------------------------------------------- #
# Key metadata
# --------------------------------------------------------------------------- #
@dataclass
class ApiKey:
    key_id: str  # truncated, for display only
    key_hash: str  # stored hash, never the actual key
    tier: KeyTier = KeyTier.FREE
    label: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_used: Optional[str] = None
    total_requests: int = 0
    revoked: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "key_id": self.key_id,
            "tier": self.tier.value,
            "label": self.label,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "total_requests": self.total_requests,
            "revoked": self.revoked,
        }


# --------------------------------------------------------------------------- #
# Rate limiter
# --------------------------------------------------------------------------- #
@dataclass
class RateLimitBucket:
    count: int = 0
    window_start: float = field(default_factory=time.time)


# --------------------------------------------------------------------------- #
# ApiKeyManager
# --------------------------------------------------------------------------- #
class ApiKeyManager:
    """
    In-memory API key management.

    - Generate new keys (returns the actual key once — only time it's shown)
    - Verify keys on each request
    - Track usage
    - Enforce rate limits per tier
    - Revoke keys

    Security: Keys are stored as SHA-256 hashes, never as plaintext.
    """

    KEY_PREFIX = "slo_"

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._keys: Dict[str, ApiKey] = {}  # key_id -> ApiKey
        self._key_hashes: Dict[str, str] = {}  # key_hash -> key_id (reverse lookup)
        self._rate_daily: Dict[str, RateLimitBucket] = {}
        self._rate_minute: Dict[str, RateLimitBucket] = {}

    def _generate_key(self) -> tuple[str, str]:
        """Generate a new random API key. Returns (key_id, full_key)."""
        raw = secrets.token_urlsafe(32)
        key_id = f"{self.KEY_PREFIX}{raw[:8]}"
        full_key = f"{self.KEY_PREFIX}{raw}"
        return key_id, full_key

    def _hash_key(self, key: str) -> str:
        """SHA-256 hash of the full key."""
        return hashlib.sha256(key.encode()).hexdigest()

    def create(
        self,
        tier: KeyTier = KeyTier.FREE,
        label: str = "",
    ) -> tuple[ApiKey, str]:
        """
        Create a new API key.

        Returns (ApiKey metadata, full_key)
        The full_key is only returned ONCE — store it securely.
        """
        key_id, full_key = self._generate_key()
        key_hash = self._hash_key(full_key)

        api_key = ApiKey(
            key_id=key_id,
            key_hash=key_hash,
            tier=tier,
            label=label,
        )

        with self._lock:
            self._keys[key_id] = api_key
            self._key_hashes[key_hash] = key_id

        return api_key, full_key

    def verify(self, key: str) -> tuple[bool, Optional[ApiKey], str]:
        """
        Verify an API key.

        Returns (is_valid, ApiKey or None, error_message)
        """
        if not key or not key.startswith(self.KEY_PREFIX):
            return False, None, "Invalid API key format"

        key_hash = self._hash_key(key)

        with self._lock:
            key_id = self._key_hashes.get(key_hash)
            if not key_id:
                return False, None, "Invalid API key"

            api_key = self._keys.get(key_id)
            if not api_key:
                return False, None, "Invalid API key"

            if api_key.revoked:
                return False, None, "API key has been revoked"

        # Update last used
        api_key.last_used = datetime.now(timezone.utc).isoformat()

        # Check rate limits
        limits = TIER_LIMITS.get(api_key.tier, TIER_LIMITS[KeyTier.FREE])

        now = time.time()
        with self._lock:
            # Daily rate limit
            daily_bucket = self._rate_daily.get(key_id)
            if daily_bucket and now - daily_bucket.window_start > 86400:
                daily_bucket = RateLimitBucket(window_start=now)
                self._rate_daily[key_id] = daily_bucket
            elif not daily_bucket:
                daily_bucket = RateLimitBucket(window_start=now)
                self._rate_daily[key_id] = daily_bucket

            daily_limit = limits["requests_per_day"]
            if daily_limit > 0 and daily_bucket.count >= daily_limit:
                return False, api_key, f"Daily rate limit exceeded ({daily_limit}/day for {api_key.tier.value} tier)"

            # Minute rate limit
            min_bucket = self._rate_minute.get(key_id)
            if min_bucket and now - min_bucket.window_start > 60:
                min_bucket = RateLimitBucket(window_start=now)
                self._rate_minute[key_id] = min_bucket
            elif not min_bucket:
                min_bucket = RateLimitBucket(window_start=now)
                self._rate_minute[key_id] = min_bucket

            min_limit = limits["requests_per_minute"]
            if min_limit > 0 and min_bucket.count >= min_limit:
                return False, api_key, f"Rate limit exceeded ({min_limit}/min for {api_key.tier.value} tier)"

            # Increment counters
            daily_bucket.count += 1
            min_bucket.count += 1
            api_key.total_requests += 1

        return True, api_key, ""

    def revoke(self, key_id: str) -> bool:
        """Revoke an API key."""
        with self._lock:
            api_key = self._keys.get(key_id)
            if not api_key:
                return False
            api_key.revoked = True
            return True

    def get(self, key_id: str) -> Optional[ApiKey]:
        with self._lock:
            return self._keys.get(key_id)

    def list(self) -> list[ApiKey]:
        with self._lock:
            return [k for k in self._keys.values() if not k.revoked]

    def stats(self) -> dict:
        with self._lock:
            active = [k for k in self._keys.values() if not k.revoked]
            by_tier = {}
            for k in active:
                by_tier[k.tier.value] = by_tier.get(k.tier.value, 0) + 1
            return {
                "total_active": len(active),
                "total_revoked": sum(1 for k in self._keys.values() if k.revoked),
                "by_tier": by_tier,
                "total_requests": sum(k.total_requests for k in self._keys.values()),
            }

    def usage(self, key_id: str) -> Optional[dict]:
        """
        Return current rate-limit usage for a key.
        Returns dict with daily/minute counters and reset timestamps, or None if key not found.
        """
        with self._lock:
            api_key = self._keys.get(key_id)
            if not api_key or api_key.revoked:
                return None

            now = time.time()
            limits = TIER_LIMITS.get(api_key.tier, TIER_LIMITS[KeyTier.FREE])

            daily_bucket = self._rate_daily.get(key_id)
            daily_used = daily_bucket.count if daily_bucket else 0
            daily_limit = limits["requests_per_day"]
            # Reset time: window_start + 86400 seconds
            daily_reset_at = None
            if daily_bucket and daily_limit > 0:
                daily_reset_at = datetime.fromtimestamp(
                    daily_bucket.window_start + 86400, tz=timezone.utc
                ).isoformat()

            minute_bucket = self._rate_minute.get(key_id)
            minute_used = minute_bucket.count if minute_bucket else 0
            minute_limit = limits["requests_per_minute"]
            minute_reset_at = None
            if minute_bucket and minute_limit > 0:
                minute_reset_at = datetime.fromtimestamp(
                    minute_bucket.window_start + 60, tz=timezone.utc
                ).isoformat()

            return {
                "tier": api_key.tier.value,
                "key_id": key_id,
                "daily_limit": daily_limit,
                "daily_used": daily_used,
                "daily_remaining": -1 if daily_limit < 0 else max(0, daily_limit - daily_used),
                "daily_reset_at": daily_reset_at,
                "minute_limit": minute_limit,
                "minute_used": minute_used,
                "minute_remaining": -1 if minute_limit < 0 else max(0, minute_limit - minute_used),
                "minute_reset_at": minute_reset_at,
                "monthly_audio_minutes_limit": limits["audio_minutes_per_month"],
                "monthly_audio_minutes_used": 0,  # TODO: wire to actual audio minutes tracker
            }


# Singleton
api_keys = ApiKeyManager()
