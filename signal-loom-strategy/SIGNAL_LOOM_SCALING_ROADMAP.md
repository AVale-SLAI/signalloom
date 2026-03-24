# Signal Loom AI — Scaling Roadmap
## From 1,000 to 10,000,000 Users: Infrastructure, Inflection Points & Unforeseen Stress

---

## Scaling Phases at a Glance

| Phase | Users | Monthly Audio Minutes | Revenue Target | Key Milestone |
|-------|-------|---------------------|----------------|---------------|
| **Alpha** | 0-1K | 0-500 min | $0 | Private beta, SDK published |
| **Beta** | 1K-10K | 500-10K min | $1-10K MRR | Landing page live, PyPI published |
| **Launch** | 10K-100K | 10K-500K min | $10K-100K MRR | YouTube integration, Stripe live |
| **Scale** | 100K-1M | 500K-10M min | $100K-1M MRR | Multi-region, enterprise tier |
| **Enterprise** | 1M-10M | 10M-100M min | $1M-10M MRR | SLA guarantees, dedicated infra |
| **Platform** | 10M+ | 100M+ min | $10M+ MRR | White-label, marketplace |

---

## Phase 1: Alpha → Beta (1K-10K Users)

### What this looks like
- Single Mac Studio M4 Max running Whisper MLX
- Local SQLite job queue (current)
- Single API server on port 18790
- serveo.net tunnel (dynamic URL) — temporary

### What breaks first

**1. Concurrent job limit (CURRENT)**
- Max 2 concurrent jobs — already a bottleneck
- **Fix:** Increase `MAX_CONCURRENT_JOBS` in core config, add job queue worker pool
- **Inflection:** At ~20 concurrent users submitting simultaneously, jobs queue up and time out

**2. In-memory job state (CRITICAL)**
- Jobs stored in Python dict — lost on server restart
- **Fix:** Move to Redis for job state, SQLite for key/auth metadata
- **Inflection:** First server restart during beta = all queued jobs vanish

**3. No persistent storage**
- Transcript JSONs written to disk but no cleanup policy
- **Fix:** Add lifecycle policy (delete transcripts >30 days old)
- **Inflection:** Disk fills up at ~10K transcripts (~500MB uncompressed)

### Kanban: Alpha → Beta

| To Do | In Progress | Done |
|-------|-------------|------|
| Landing page live | Move job state to Redis | Landing page v1 |
| PyPI SDK published | Stripe checkout integration | API key auth |
| Redis job queue | Lifecycle cleanup policy | Rate limiting (429) |
| Persistent transcript storage | YouTube URL ingest (V1.3) | GET /v1/limits endpoint |
| `MAX_CONCURRENT_JOBS` increased to 10 | | SSRF protection |
| Static public URL (ngrok/production) | | FUD security audit |
| | | Python SDK published |

**Estimated build time for Beta blockers:** 1-2 weeks

---

## Phase 2: Beta → Launch (10K-100K Users)

### What this looks like
- 10-100 concurrent transcription jobs
- 500K-5M audio minutes/month processed
- First paying customers, first churn
- Multiple users hitting rate limits actively

### What breaks first

**1. MLX GPU memory exhaustion**
- Mac Studio M4 Max has unified memory limits
- With 10+ concurrent jobs, Whisper MLX memory pressure causes OOM crashes
- **Fix:** Job concurrency limit + memory monitoring + graceful degradation
- **Inflection:** At ~50 concurrent 20-min audio files, system stalls

**2. No CDN / static asset delivery**
- Landing page served from local Python HTTP server
- No edge caching for API docs
- **Fix:** Cloudflare Pages for landing, Cloudflare for API edge (workers)
- **Inflection:** First viral tweet/HN post = landing page goes down

**3. No webhook reliability**
- Webhooks fire-and-forget, no retry queue
- If customer endpoint is down, transcript is lost
- **Fix:** Webhook retry queue with exponential backoff (3 retries over 1hr)
- **Inflection:** First paying customer misses webhook = churn signal

**4. No usage metering / billing accuracy**
- Current metrics track requests, not audio minutes accurately
- **Fix:** Add `audio_seconds` tracking per job, reconcile with tier limits
- **Inflection:** First billing dispute (customer says "I only used 80 min but you charged me for 120")

**5. Stripe webhook security**
- No signature verification on Stripe webhooks
- **Fix:** Verify `stripe-signature` header on all webhook calls
- **Inflection:** First fraudulent Stripe event = financial exposure

### Kanban: Beta → Launch

| To Do | In Progress | Done |
|-------|-------------|------|
| Redis job queue | MLX memory management | In-memory job queue |
| Webhook retry queue | Stripe webhook verification | API key auth |
| Usage metering (audio sec) | Multi-region CDN setup | Rate limiting |
| Cloudflare Pages (landing) | Stripe checkout (paid tiers) | Python SDK |
| Cloudflare Workers (API edge) | ngrok/static URL | Landing page |
| OOM crash recovery | | /v1/limits endpoint |
| Cleanup lifecycle policy | | |

**Estimated build time for Launch blockers:** 4-8 weeks

---

## Phase 3: Launch → Scale (100K-1M Users)

### What this looks like
- 1,000-10,000 concurrent users
- 100+ transcription jobs/minute
- Multiple Mac Studio machines in RDMA cluster
- Multi-tier pricing fully operational

### What breaks first

**1. Single-node Whisper MLX cannot scale**
- Even with RDMA cluster, one machine's GPU is the bottleneck
- **Fix:** Horizontal scaling — multiple MLX worker machines, job queue distributes work
- **Inflection:** At ~500 jobs/minute, one Mac Studio is fully saturated

**2. No database = no analytics**
- Without a real DB, we can't answer: "Who are our top 10 customers by usage?"
- **Fix:** PostgreSQL for all metadata (jobs, keys, usage, billing)
- **Inflection:** First enterprise sales cycle requires usage reports we can't generate

**3. No SLA guarantees**
- Free/SMB tiers have no uptime commitment
- **Fix:** Status page (statuspage.io or self-hosted), uptime monitoring, incident response
- **Inflection:** First customer asks "what's your SLA?" in a sales call

**4. API rate limit granularity is too coarse**
- Per-key rate limits exist but no burst protection
- **Fix:** Token bucket algorithm per key, Redis-backed
- **Inflection:** A customer on Scale tier hammers the API at 10x their tier limit during a product launch

**5. No multi-region redundancy**
- All processing on Mac Studio cluster in one location
- **Fix:** Multi-region deployment (AWS/GCP), geolocation-based routing
- **Inflection:** Any regional outage = total downtime

### Kanban: Launch → Scale

| To Do | In Progress | Done |
|-------|-------------|------|
| Horizontal MLX scaling | PostgreSQL migration | Redis job queue |
| Multi-region deployment | Token bucket rate limiting | Webhook retry queue |
| Status page | SLA documentation | Stripe webhook verification |
| Enterprise tier (custom SLAs) | Usage analytics dashboard | Cloudflare CDN |
| PostgreSQL + ORM (SQLAlchemy) | | |

**Estimated build time for Scale blockers:** 3-6 months

---

## Phase 4: Scale → Enterprise (1M-10M Users)

### What this looks like
- Enterprise customers with 100K+ employees
- White-label deals with SaaS platforms reselling Signal Loom
- Annual contracts, custom pricing, dedicated infrastructure
- Compliance requirements: SOC 2, HIPAA, GDPR

### What breaks first

**1. Apple Silicon MLX hits GPU ceiling**
- Even M4 Ultra has finite MLX throughput
- **Fix:** CUDA GPU fleet (NVIDIA A100/H100) for heavy workloads, MLX for free tier
- **Inflection:** Enterprise customer with 1M min/month demand cannot be served on MLX

**2. Data residency requirements**
- Enterprise customers in EU require EU data processing
- **Fix:** EU region deployment, GDPR compliance documentation
- **Inflection:** First EU enterprise deal blocked by data residency

**3. SOC 2 Type II compliance**
- Startup-pitch compliance isn't enough at this scale
- **Fix:** SOC 2 Type II audit, penetration testing, security review
- **Inflection:** First enterprise procurement cycle requires SOC 2 Type II

**4. White-label infrastructure**
- A SaaS company wants to resell Signal Loom under their brand
- **Fix:** API key system supports sub-accounts, reseller billing, custom SLAs
- **Inflection:** First white-label deal negotiation

**5. Support SLA mismatch**
- 24hr email support doesn't work for enterprise
- **Fix:** Dedicated support channel, 99.9% uptime SLAs with financial penalties
- **Inflection:** First P1 outage at an enterprise customer

### Kanban: Scale → Enterprise

| To Do | In Progress | Done |
|-------|-------------|------|
| CUDA GPU fleet (cloud) | SOC 2 Type II audit | Horizontal MLX scaling |
| EU region deployment | White-label sub-account system | Multi-region |
| 99.9% SLA contracts | Dedicated support channel | PostgreSQL |
| Penetration testing | Enterprise billing (annual) | Token bucket |
| SOC 2 Type II | GDPR DPA documentation | |

---

## The 6 Unforeseen Stress Inflection Points

These are the "unknown unknowns" — the problems that feel far away but will hit harder than expected:

### 1. **Audio file storage cost grows linearly with users**
- Every uploaded file is stored until job completes + 30-day retention
- At 1M users × 50MB avg upload × 30 days = massive storage bill
- **Mitigation:** Aggressive cleanup (24hr post-completion), object storage (S3 R2) with lifecycle rules
- **Signal:** Watch storage costs monthly — if growing faster than revenue, compression or cleanup is overdue

### 2. **Malicious users / API abuse**
- Free tier: 100 min/month, 10 req/min
- A bad actor spins up 100 fake accounts → 10K free minutes/month
- **Mitigation:** Credit card verification for free tier (V1.2), anomaly detection on usage patterns
- **Signal:** Sudden spike in free-tier API calls without corresponding conversion

### 3. **The "Slack effect" — virality is a double-edged sword**
- One famous AI developer tweets about Signal Loom → massive spike in signups
- Our system isn't ready → downtime on the most visible day of our existence
- **Mitigation:** Pre-scale to 10x expected load before any public launch announcement
- **Signal:** Watch referral traffic spikes — every spike needs proactive scaling

### 4. **Whisper model licensing uncertainty**
- OpenAI's Whisper model has an MIT license for the weights — but this could change
- MLX community models are derivative — their licensing inherits uncertainty
- **Mitigation:** Architecture must be model-agnostic (abstraction layer between API and model)
- **Signal:** Any Whisper license change → immediate architectural review required

### 5. **The "Zombie job" problem**
- User submits a job, never retrieves result, never cancels
- Job sits in queue forever, consuming memory and disk
- **Mitigation:** Auto-cancel jobs after 7 days of inactivity, TTL on all job states
- **Signal:** Queue depth growing without corresponding active users

### 6. **The free-tier trap**
- Free tier has no credit card — we have no way to charge for overages
- Customer uses 100 min, then upgrades to $9/mo plan
- If they cancel, Stripe can't re-charge the difference
- **Mitigation:** Clear overage policy communicated upfront, hard limits enforced at API level
- **Signal:** Churned customers with "I didn't know I'd be charged" complaints

---

## Capacity Planning Reference Table

| Users | Concurrent Jobs | Storage (30-day) | Monthly Compute Cost | Bandwidth |
|-------|----------------|-----------------|---------------------|-----------|
| 1K | 5-10 | 5 GB | $0 (MLX, local) | $5 |
| 10K | 20-50 | 50 GB | $50 (cloud GPU burst) | $50 |
| 100K | 100-500 | 500 GB | $500-2K | $500 |
| 1M | 500-5,000 | 5 TB | $5K-20K | $5K |
| 10M | 5,000-50,000 | 50 TB | $50K-200K | $50K |

**Revenue needed to break even at each tier:** At 40% gross margins, revenue = 1.67x compute cost

---

## Quality Gates (Required Before Each Phase)

| Phase | Quality Gate |
|-------|-------------|
| Alpha → Beta | 100% of SDK tests passing, P0 security audit clean, 429 rate limit working |
| Beta → Launch | Webhook retry queue, Stripe signature verified, <30min incident response |
| Launch → Scale | PostgreSQL live, SLA docs ready, multi-region failover tested |
| Scale → Enterprise | SOC 2 Type I complete, EU data residency confirmed, 99.9% SLA contracts |

