# Signal Loom AI — Admin / Key Management Router
"""
POST /v1/keys — Create a new API key
GET  /v1/keys — List active API keys
DELETE /v1/keys/{key_id} — Revoke an API key
GET  /v1/keys/{key_id}/stats — Get stats for a specific key
GET  /v1/metrics — Get usage metrics
GET  /v1/metrics/summary — Get summary dashboard
GET  /v1/webhooks — List webhook deliveries
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from schemas import APIError
from webhooks.api_keys import api_keys, KeyTier, TIERS as KEY_TIERS
from monitoring import metrics

router = APIRouter()


# --------------------------------------------------------------------------- #
# API Keys
# --------------------------------------------------------------------------- #
@router.post("/keys")
async def create_key(
    request: Request,
    tier: str = Query(default="free", description="Tier: free, starter, pro, scale, enterprise"),
    label: str = Query(default="", description="Label for this key (e.g. 'dev', 'production')"),
) -> dict:
    """
    Create a new API key.

    The full key is returned ONLY once. Store it securely.
    This is the only time the full key will be shown.

    For free tier signup (beta), also include email and name in the JSON body:
    {"email": "you@example.com", "name": "Your Name"}

    Tiers:
    - free: 100 requests/day, 10/min, 100 audio min/month (no credit card)
    - starter: 1,000/day, 50/min, 10,000 audio min/month ($25/mo)
    - pro: 10,000/day, 200/min, 100,000 audio min/month ($99/mo)
    - scale: 100,000/day, 1,000/min, 1,000,000 audio min/month ($349/mo)
    - enterprise: unlimited (contact for pricing)
    """
    try:
        tier_enum = KeyTier(tier.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid tier: {tier}. Valid: free, starter, pro, scale, enterprise"
        )

    # Capture email if provided in JSON body (free tier signup)
    email = None
    name = None
    try:
        body = await request.json()
        email = body.get("email", "")
        name = body.get("name", "")
    except Exception:
        pass

    # Use name/label as email if provided for free tier
    display_label = label or name or ""
    if email:
        display_label = f"{display_label} <{email}>" if display_label else email

    api_key, full_key = api_keys.create(tier=tier_enum, label=display_label)

    return {
        "ok": True,
        "api_key": full_key,
        "key": api_key.to_dict(),
        "tier": tier.lower(),
        "tier_limits": {
            "requests_per_day": KEY_TIERS[tier_enum]["requests_per_day"],
            "requests_per_minute": KEY_TIERS[tier_enum]["requests_per_minute"],
            "audio_minutes_per_month": KEY_TIERS[tier_enum]["audio_minutes_per_month"],
        },
    }


@router.get("/keys")
def list_keys() -> dict:
    """List all active (non-revoked) API keys."""
    keys = api_keys.list()
    return {
        "keys": [k.to_dict() for k in keys],
        "total": len(keys),
    }


@router.delete("/keys/{key_id}")
def revoke_key(key_id: str) -> dict:
    """Revoke an API key."""
    success = api_keys.revoke(key_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Key not found: {key_id}")
    return {"ok": True, "key_id": key_id, "status": "revoked"}


@router.get("/keys/{key_id}/stats")
def key_stats(key_id: str) -> dict:
    """Get detailed stats for a specific API key."""
    key = api_keys.get(key_id)
    if not key:
        raise HTTPException(status_code=404, detail=f"Key not found: {key_id}")
    return {
        "key": key.to_dict(),
        "tier_limits": KEY_TIERS.get(key.tier, KEY_TIERS[KeyTier.FREE]),
    }


# --------------------------------------------------------------------------- #
# Metrics
# --------------------------------------------------------------------------- #
@router.get("/metrics/summary")
def metrics_summary() -> dict:
    """Get usage metrics summary."""
    return metrics.get_summary()


@router.get("/metrics/daily")
def metrics_daily(days: int = Query(default=7, ge=1, le=90)) -> dict:
    """Get daily metrics for the last N days."""
    daily = metrics.get_recent_daily_stats(days=days)
    return {
        "days": [d.date for d in reversed(daily)],
        "metrics": [
            {
                "date": d.date,
                "requests": d.total_requests,
                "jobs": d.total_jobs,
                "chars": d.total_chars,
                "duration_seconds": round(d.total_duration_seconds, 1),
                "successful": d.successful_jobs,
                "failed": d.failed_jobs,
                "avg_latency_ms": round(d.avg_latency_ms, 1),
                "p95_latency_ms": round(d.p95_latency_ms, 1),
                "p99_latency_ms": round(d.p99_latency_ms, 1),
            }
            for d in reversed(daily)
        ],
    }


# --------------------------------------------------------------------------- #
# Webhooks
# --------------------------------------------------------------------------- #
@router.get("/webhooks")
def list_webhooks(
    limit: int = Query(default=50, ge=1, le=500),
) -> dict:
    """List recent webhook deliveries."""
    all_webhooks = webhooks.get_all()
    sorted_webhooks = sorted(
        all_webhooks,
        key=lambda w: w.created_at,
        reverse=True,
    )[:limit]
    return {
        "webhooks": [w.to_dict() for w in sorted_webhooks],
        "total": len(all_webhooks),
    }


# --------------------------------------------------------------------------- #
# System info
# --------------------------------------------------------------------------- #
@router.get("/info")
def system_info() -> dict:
    """Get system information and configuration."""
    from core import (
        DEFAULT_MODEL, SUPPORTED_MODELS, MAX_CONCURRENT_JOBS,
        WORKSPACE, UPLOAD_DIR, TRANSCRIPTS_DIR,
    )
    return {
        "version": "0.1.0-alpha",
        "default_model": DEFAULT_MODEL,
        "supported_models": SUPPORTED_MODELS,
        "max_concurrent_jobs": MAX_CONCURRENT_JOBS,
        "workspace": str(WORKSPACE),
        "upload_dir": str(UPLOAD_DIR),
        "transcripts_dir": str(TRANSCRIPTS_DIR),
    }
