# Signal Loom AI — Staff & Support Training Manual
**Version 1.0 | 2026-03-28 | For internal use and sub-agent training**

---

## What Signal Loom AI Actually Is

Signal Loom AI ingests audio and video — YouTube URLs, uploaded files, live streams — and returns a **structured knowledge object** (timestamped, speaker-labeled, entity-enriched JSON) instead of raw transcript text.

The product is not transcription. The product is structured intelligence that AI systems can actually use.

---

## System Architecture

```
Buyer/User
    ↓
signalloomai.com (static landing)
    ├── /signup.html         → creates free account
    ├── /checkout.html       → Stripe checkout → paid tier
    ├── /ingest.html        → live demo (YouTube URL → JSON)
    ├── /builders.html       → primary ICP page
    ├── /meetings.html       → whitepaper: RAG/meetings
    ├── /youtube-archive.html → whitepaper: content ops
    └── /voice-agents.html   → whitepaper: voice AI

API: api.signalloomai.com
    ├── POST /v1/account              → create account + API key
    ├── POST /v1/transcribe           → submit file or URL
    ├── GET  /v1/result/{job_id}      → poll result
    ├── WS   /v1/ws/stream            → real-time WebSocket streaming
    ├── POST /v1/stripe/checkout      → create Stripe checkout session
    ├── GET  /v1/stripe/usage         → rate limit status
    └── POST /v1/stripe/webhook       → Stripe subscription events

Worker: Whisper ML inference (subprocess, Mac mini)
    └── Max 3 concurrent jobs (prevents CPU saturation)

Storage:
    ├── SQLite: api_keys, jobs table
    ├── /uploads/: raw uploaded files
    └── /processed/: JSON/SRT/VTT output
```

---

## Complete End-to-End User Flow

### Flow 1: Free Tier (Self-Serve)

**Step 1 — Sign up**
```
User → /signup.html → POST /v1/account {email, name}
Response: { api_key: "slo_...", tier: "free" }
```
- User gets API key displayed on screen (shown once)
- Key stored in localStorage as `sl_api_key`
- Free tier: 100 requests/day, 10 requests/minute

**Step 2 — First transcription**
```
User → POST /v1/transcribe
  Authorization: Bearer {api_key}
  url=https://youtube.com/watch?v=...  OR  file={audio_file}
  return_format=json  (default: json)
Response: { job_id: "uuid", status: "queued" }
```
- YouTube: yt-dlp downloads audio → Whisper processes → JSON returned
- File: uploaded → validated (magic bytes, not just extension) → Whisper → JSON
- Typical processing: ~4-5x realtime (213s audio ≈ 45s processing)

**Step 3 — Poll for result**
```
User → GET /v1/result/{job_id}
  Authorization: Bearer {api_key}
Response: {
  job_id: "...",
  status: "completed",
  transcript: {
    schema: "Signal Loom Schema v1",
    source_ref: "youtube.com/watch?v=...",
    source_kind: "youtube_url",
    duration_seconds: 213.04,
    language: "en",
    segments: [
      {
        segment_id: "S1",
        start_seconds: 0.0,
        end_seconds: 21.88,
        text: "We're no strangers to love..."
      },
      ...
    ],
    metadata: {
      ffprobe: { media_kind: "audio", duration_seconds: 213.04, format_name: "mp3" }
    }
  },
  raw_text: "...",
  srt: "...",
  vtt: "...",
  download_url: "/v1/download/{job_id}"
}
```

**Step 4 — Get download**
```
GET /v1/download/{job_id}?format={json|srt|vtt|txt}
```
Returns the requested format file.

---

### Flow 2: Paid Upgrade (Self-Serve)

**Step 1 — View plans**
```
User → /checkout.html
  (No login required to view)
```

**Step 2 — Select plan and pay**
```
User selects tier (Starter $25 / Pro $99 / Scale $349)
→ POST /v1/stripe/checkout
  tier=pro
  success_url=https://signalloomai.com/account.html?upgraded=pro
  cancel_url=https://signalloomai.com/checkout.html
Response: { checkout_url: "https://checkout.stripe.com/c/pay/cs_live_..." }
→ User lands on Stripe Checkout → enters card → pays
```

**Step 3 — Stripe webhook fires**
```
Stripe → POST /v1/stripe/webhook
  event: checkout.session.completed
  ↓
  Stripe webhook verified via whsec_... signature
  ↓
  Account upgraded to paid tier
  ↓
  Paid API key activated
```

**Step 4 — Access granted**
```
User → /account.html (auto-redirects after successful payment)
→ New tier limits active:
  - Starter: 1000 min/mo, 1 concurrent job
  - Pro: 5000 min/mo, 5 concurrent jobs
  - Scale: 25000 min/mo, 15 concurrent jobs
```

---

### Flow 3: WebSocket Streaming

**Use case:** Voice agents, live transcription, real-time features

```
Client → WebSocket /v1/ws/stream
  Headers: Authorization: Bearer {api_key}
  Body: { audio_chunk: <bytes>, format: "raw" }

Server streams back:
  { type: "transcript", text: "Thank", start_seconds: 0.0, end_seconds: 0.32, language: "en", done: false }
  { type: "transcript", text: "Thank you.", start_seconds: 0.0, end_seconds: 0.58, language: "en", done: true }
  ... (partial results as audio is processed)

done: false = segment still being processed
done: true  = segment finalized, text stable
```

---

## All Error Codes

### HTTP Status Codes

| Code | Meaning | Common Cause | Resolution |
|------|---------|--------------|------------|
| **200** | Success | Request completed normally | ✅ Normal |
| **400** | Bad Request | Malformed URL, invalid format, missing field | Check request body/params |
| **401** | Unauthorized | Missing or invalid API key | Provide valid Bearer token |
| **403** | Forbidden | Valid key but insufficient tier | Upgrade plan |
| **404** | Not Found | Job ID doesn't exist or not yet available | Poll again or check job_id |
| **409** | Conflict | Duplicate job submission | Use existing job_id |
| **413** | Payload Too Large | File > 100MB | Split audio or reduce size |
| **415** | Unsupported Media | File type not supported | Use mp3/mp4/m4a/wav/ogg/flac/mov/avi/mkv/webm |
| **422** | Unprocessable Entity | SSRF blocked (private IP URL), invalid YouTube ID | Use public URL |
| **429** | Rate Limited | Too many requests per minute or per day | Wait, upgrade tier |
| **500** | Internal Error | Unexpected server error | Report to support |
| **502** | Bad Gateway | Upstream service failure (yt-dlp, Whisper) | Retry, check system |
| **503** | Service Unavailable | System overloaded (queue full) | Retry after delay |
| **000** | Connection Failed | Request timed out waiting for queue slot, or API down | Check API status |

---

### Application Error Codes (`failure_code` field)

These appear in the JSON response body under `failure_code`:

| Code | Meaning | Cause | Resolution |
|------|---------|-------|------------|
| `RATE_LIMITED` | Rate limit hit | Too many requests for tier | Wait or upgrade |
| `INVALID_API_KEY` | Key not recognized | Key revoked, deleted, or never existed | Create new key |
| `API_KEY_REVOKED` | Key was revoked | Account suspended | Contact support |
| `QUOTA_EXCEEDED` | Daily/minute quota hit | Usage exhausted | Wait for reset or upgrade |
| `DOWNLOAD_FAILED` | yt-dlp could not fetch URL | Video unavailable, private, age-restricted | Try different URL |
| `TRANSCRIPTION_FAILED` | Whisper processing error | Corrupt audio, unsupported codec | Re-encode audio |
| `FILE_TOO_LARGE` | File exceeds 100MB | Oversized upload | Split or compress |
| `UNSUPPORTED_FORMAT` | File type not supported | Bad extension or corrupt file | Convert to supported format |
| `SSRF_BLOCKED` | Private/internal URL detected | URL points to private network | Use public URL |
| `SCAN_FAILED` | Security scan detected threat | File flagged as malicious | Upload different file |
| `TIER_REQUIRED` | Feature not available on current tier | e.g. Webhook on free tier | Upgrade |

---

### Stripe Error Codes

| Code | Meaning | Resolution |
|------|---------|------------|
| `card_declined` | Card was declined | Buyer uses different card |
| `card_expired` | Card expiry passed | Update payment method |
| `insufficient_funds` | No funds available | Buyer contacts bank |
| `invalid_email` | Stripe can't deliver receipt | Use valid email |
| `checkout_expired` | Checkout session timed out (>24h) | Start new checkout |
| `already_subscribed` | Attempted duplicate subscription | No action needed |
| `webhook_verification_failed` | Stripe signature mismatch | Check webhook secret in .env |

---

## Rate Limits by Tier

| Tier | Requests/Minute | Requests/Day | Structured Minutes/Month |
|------|----------------|--------------|------------------------|
| Free | 10 | 100 | 100 |
| Starter ($25) | 30 | 1,000 | 1,000 |
| Pro ($99) | 60 | 5,000 | 5,000 |
| Scale ($349) | 150 | 25,000 | 25,000 |

**Note:** `requests/minute` is per-api-key. Bursting above the limit returns HTTP 429 immediately.

---

## Escalation Chain

### Tier 1 — User Self-Service (No Staff Action Required)

These issues resolve without intervention:
- Rate limit hit → user waits, tier upgrade resolves
- Job still queued → normal; processing is 4-5x realtime
- Checkout redirect issue → user clears cache, retries
- Invalid API key → user regenerates at /account.html

### Tier 2 — Staff Can Resolve

**API not responding (HTTP 000/503)**
1. Check if API process is running: `curl api.signalloomai.com/health`
2. Check if workers are saturated: `/v1/queue/status`
3. Restart if needed: `kill uvicorn PID && restart via start.sh`

**Transcription stuck / job not completing**
1. Check queue depth and active jobs
2. If queue > 10, workers may be backed up — normal under load
3. If job stuck > 30 min, check Whisper process: `ps aux | grep whisper`
4. Cancel stuck job and resubmit

**Stripe webhook not firing**
1. Check Stripe Dashboard → Developers → Webhooks
2. Confirm endpoint `https://api.signalloomai.com/v1/stripe/webhook` is active
3. Check webhook secret matches `whsec_...` in `.env`
4. Check recent webhook events in Stripe Dashboard for failure logs

**User can't upgrade / key not activating**
1. Verify payment went through in Stripe Dashboard → Payments
2. Check if webhook fired: Stripe Dashboard → Developers → Webhook events
3. If webhook missed, manually upgrade via Stripe portal or DB

**Rate limit not resetting**
1. Rate limits reset at midnight UTC
2. Daily reset is automatic
3. Minute limit resets after 60 seconds

### Tier 3 — Requires Traves/Aster Intervention

**System stability under load (API becomes unresponsive)**
- Symptom: API stops accepting connections (curl hangs), health check fails
- Cause: ML workers blocking uvicorn event loop
- Fix: Hard kill stuck processes, restart API with `MAX_CONCURRENT_JOBS=3`
- Long-term fix: Move ML inference to separate process pool (architecture work)

**Database corruption or key loss**
- SQLite at `signal-loom-api/signal_loom.db`
- Full backup exists at `~/cold-tier/backups/openclaw/signal-loom/`
- On corruption: restore from latest backup, restart API

**Webhook secret leak or compromise**
- Rotate immediately in Stripe Dashboard
- Update `STRIPE_WEBHOOK_SECRET` in `.env`
- Restart API

**Security incident (SSRF success, file upload exploit, key brute force)**
1. Isolate: take API offline immediately
2. Assess: check logs for scope of breach
3. Contain: revoke compromised keys, block attacking IPs
4. Recover: restore from known-good state
5. Notify: if PII/HIPAA exposure, follow legal obligations

---

## Sub-Agent Training: How to Use Signal Loom API

### Step 1: Get an API Key

```python
import requests

email = "your-subagent@yourcompany.com"
name = "Sub-Agent Name"

resp = requests.post(
    "https://api.signalloomai.com/v1/account",
    json={"email": email, "name": name}
)
api_key = resp.json()["api_key"]
print(f"API Key: {api_key}")
```

**Store the API key securely.** It is shown only once on creation.

---

### Step 2: Transcribe a YouTube URL

```python
import requests, time

api_key = "slo_your_key_here"

# Submit job
resp = requests.post(
    "https://api.signalloomai.com/v1/transcribe",
    headers={"Authorization": f"Bearer {api_key}"},
    data={"return_format": "json"},
    files={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
)
job = resp.json()
job_id = job["job_id"]
print(f"Job queued: {job_id}")

# Poll for result (wait ~45s for 3-min audio)
for attempt in range(30):
    time.sleep(5)
    result = requests.get(
        f"https://api.signalloomai.com/v1/result/{job_id}",
        headers={"Authorization": f"Bearer {api_key}"}
    ).json()
    if result.get("status") == "completed":
        print(f"Done! Segments: {len(result['transcript']['segments'])}")
        break
    elif result.get("status") == "failed":
        print(f"Failed: {result.get('failure_code')}")
        break
```

---

### Step 3: Handle Errors Gracefully

```python
import requests

api_key = "slo_your_key_here"
url = "https://api.signalloomai.com/v1/transcribe"

def transcribe(url_or_file, is_url=True):
    try:
        if is_url:
            resp = requests.post(url,
                headers={"Authorization": f"Bearer {api_key}"},
                data={"return_format": "json"},
                files={"url": url_or_file}
            )
        else:
            resp = requests.post(url,
                headers={"Authorization": f"Bearer {api_key}"},
                data={"return_format": "json"},
                files={"file": open(url_or_file, "rb")}
            )

        # Handle HTTP errors
        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 60))
            print(f"Rate limited. Retry after {retry_after}s")
            return None

        if resp.status_code == 422:
            print(f"SSRF blocked or invalid URL: {resp.json()}")
            return None

        if resp.status_code == 413:
            print(f"File too large (max 100MB)")
            return None

        resp.raise_for_status()
        return resp.json()

    except requests.exceptions.Timeout:
        print("Request timed out — system may be overloaded")
        return None
    except requests.exceptions.ConnectionError:
        print("Connection failed — API may be down")
        return None
```

---

### Step 4: Check Your Usage / Rate Limits

```python
import requests

api_key = "slo_your_key_here"
usage = requests.get(
    "https://api.signalloomai.com/v1/stripe/usage",
    headers={"Authorization": f"Bearer {api_key}"}
).json()

print(f"Tier: {usage['tier']}")
print(f"Daily remaining: {usage['daily_remaining']}/{usage['daily_limit']}")
print(f"Minute remaining: {usage['minute_remaining']}/{usage['minute_limit']}")
print(f"Resets at: {usage['daily_reset_at']}")
```

---

## Common Support Scenarios

### Scenario 1: "My transcription is taking too long"
**Normal:** 4-5x realtime. 3-minute audio ≈ 45 seconds.
**If stuck > 5 min:** Check queue depth. May be a system backup.
**If stuck > 30 min:** Check Whisper process. Job may have crashed — restart API.

### Scenario 2: "I got rate limited but I only sent a few requests"
**Cause:** Free tier is 10 req/min. If you submitted multiple concurrent requests (e.g., from a loop), you hit the limit immediately.
**Fix:** Wait 60 seconds, or upgrade to Pro (60 req/min).

### Scenario 3: "My YouTube URL says 'Download failed'"
**Causes:** Video is private, age-restricted, region-blocked, or deleted.
**Not our bug:** yt-dlp fails because the source is unavailable.
**Fix:** Try a different video, or upload the audio file directly.

### Scenario 4: "I paid but my account didn't upgrade"
**Check:** Stripe Dashboard → Payments → confirm charge succeeded.
**Then check:** Stripe Dashboard → Developers → Webhooks → confirm events fired.
**If webhook missed:** Manually upgrade via Stripe customer portal, or contact Aster.

### Scenario 5: "I'm getting HTTP 000 when I try to transcribe"
**Cause:** System is overloaded and couldn't accept the connection within 30s.
**Fix:** Wait 30 seconds and retry. If it persists, escalate to Tier 3.

### Scenario 6: "Invalid API key format" on a valid key
**Cause:** The key was created but the API restarted before keys were persisted to DB, or key was revoked.
**Fix:** Create a new account/key at /signup.html.

### Scenario 7: "Webhook says signature verification failed"
**Cause:** Webhook secret in `.env` doesn't match Stripe Dashboard.
**Fix:** Update `STRIPE_WEBHOOK_SECRET` in `.env` with current value from Stripe Dashboard → Developers → Webhooks.

---

## System Limits Reference

| Resource | Limit |
|----------|-------|
| Max file upload size | 100MB |
| Concurrent ML workers | 3 (Mac mini) |
| Max job queue depth | Unlimited (jobs queue, wait) |
| Max YouTube URL length | 2048 chars |
| Max concurrent WebSocket connections | ~5 under load |
| API request timeout | 30s (returns 000 if exceeded) |
| Max file formats | mp3, mp4, m4a, wav, ogg, flac, mov, avi, mkv, webm |

---

## File Locations

| File | Path |
|------|------|
| API main | `signal-loom-api/main.py` |
| Auth middleware | `signal-loom-api/middleware/auth.py` |
| API keys DB | `signal-loom-api/signal_loom.db` |
| Environment config | `signal-loom-api/.env` |
| Upload storage | `signal-loom-api/uploads/` |
| Transcript output | `signal-loom-api/processed/` |
| API startup script | `signal-loom-api/start.sh` |
| Landing pages | `signal-loom-landing/` |
| Daily backups | `~/cold-tier/backups/openclaw/signal-loom/` |

---

## Contacts

| Role | Contact |
|------|---------|
| Technical escalation | Aster (this system) |
| Billing / Stripe issues | Traves |
| Security incidents | Aster + Traves |
| Product feedback | Traves |

---

*Document version: 1.0 | Last updated: 2026-03-28 | Owner: Aster Vale*
