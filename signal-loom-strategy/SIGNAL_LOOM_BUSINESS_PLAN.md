# Signal Loom AI — Business Plan Overview
## Living Document | Version 1.0 | March 2026

> *"Media In. Machine Intelligence Out."*

---

## 1. Executive Summary

### What We Are
Signal Loom AI is an API-first transcription infrastructure company. We convert audio and video into structured, agent-readable knowledge objects — not raw text. Our customers are developers, AI agent builders, SaaS platforms, and vertical SaaS companies who need a reliable, cost-efficient transcription pipeline as a component of their product.

### The Core Bet
Every major AI application — agents, RAG pipelines, call intelligence tools, content platforms — needs to ingest voice/audio. The companies that own that ingestion layer, and do it with structured output that AI systems can actually use, will become the utilities of the AI era.

We are building that utility.

### The Immediate Product
- **API server** that accepts audio/video → returns structured JSON (entities, topics, sentiment, timestamps, summary)
- **Python SDK** on PyPI (`pip install signalloom`)
- **Free tier:** 100 audio min/month, no credit card
- **Paid tiers:** Starter $25/mo · Pro $99/mo · Scale $349/mo · Enterprise: contact

### Current State (March 2026)
- API server: live, tested, 0.1.0-alpha
- Python SDK: built, packaged, awaiting PyPI publish (needs token)
- Landing page: built, all links fixed, awaiting Cloudflare deploy
- Security audit: passed (FUD-level adversarial review)
- Revenue: $0 (pre-launch)

---

## 2. Mission & Vision

**Mission:** Make every minute of audio and video computationally accessible to AI systems.

**Vision:** Every AI agent, every RAG pipeline, every voice interface in the world runs on structured audio intelligence from Signal Loom.

**Three-year goal:** $1M ARR, 500+ paying customers, established as the developer首选 transcription infrastructure.

---

## 3. Product Architecture

### Current Stack
```
Audio/Video Input
      ↓
Cloudflare Pages (landing/signup) → Stripe (paid tiers)
      ↓
FastAPI API Server (port 18790)
  ├── Bearer Token Auth (SHA-256 hashed keys)
  ├── SSRF Protection
  ├── Rate Limiting (429 + Retry-After)
  ├── Language Command Injection Prevention
  └── File Size Enforcement
      ↓
Whisper MLX (Apple Silicon)
  ├── MLX Community Whisper Large V3 Turbo (default)
  └── MLX Community Whisper Large V3 (high accuracy)
      ↓
Structured JSON Output
  ├── Entities (people, places, orgs, products)
  ├── Topics and Keywords
  ├── Sentiment per segment
  ├── Timestamps (segment-level + word-level)
  ├── Summary
  └── Normalized text
```

### Product Versions (Stair-Step Plan)

| Version | Target | Status |
|---------|--------|--------|
| V0.1.0-alpha | Private beta, internal testing | ✅ Done |
| V1.0 | Public API, Python SDK, landing page | 🚧 Landing + SDK pending publish |
| V1.1 | Sync + batch endpoints, language auto-detect | ✅ Done |
| V1.2 | Speaker diarization, topic/entity tags | 📋 Planned |
| V1.3 | Webhooks, streaming, YouTube/URL ingest | 📋 Planned |
| V2.0 | MCP Server, LangChain Tool, n8n Node | 📋 Planned |

---

## 4. Market Analysis

### Total Addressable Market (TAM)
| Segment | TAM Estimate | Our Position |
|---------|-------------|---------------|
| AI Agent Memory / RAG pipelines | $2.5B (2025) | Primary target |
| Call Intelligence (sales/contact center) | $4.2B | Secondary |
| Podcast / video content tools | $2B+ | Wedge market |
| Legal transcription | $2B | Year 2+ |
| Medical/healthcare documentation | $5B | AEHS adjacency |
| Educational content indexing | $77B | Long horizon |

### Target Customer Profile
**Primary ICP (Developer/API-first):**
- Individual developers building AI apps (40%)
- Small AI startups (30%)
- Indie hackers and bootstrapped founders (20%)
- Growth/RevOps teams at SMBs (10%)

**Secondary ICP (Enterprise/Platform):**
- SaaS platforms reselling transcription (Year 2+)
- Enterprise vertical SaaS (legal, medical, contact center)

### Competitive Landscape
Signal Loom's structural advantages:
1. **MLX-local processing** — no per-minute cloud API costs → 70%+ margin at any price point vs competitors' 20-40% margins
2. **Structured output designed for AI** — not an afterthought, not an add-on
3. **API-first everything** — docs, SDK, webhooks, OpenAPI spec are all first-class
4. **Developer community positioning** — we belong where developers congregate, not where sales teams close enterprise deals

---

## 5. Revenue Model

### Pricing Architecture
| Tier | Price | Audio Min/Mo | Req/Day | Req/Min | Target |
|------|-------|-------------|---------|---------|--------|
| Free | $0 | 100 min | 100 | 10 | Developer sandbox |
| Starter | $25/mo | 10K min | 1K | 50 | Indie devs, small teams |
| Pro | $99/mo | 100K min | 10K | 200 | Startups, growth teams |
| Scale | $349/mo | 1M min | 100K | 1,000 | Productized services |
| Enterprise | Custom | Unlimited | -1 | -1 | SaaS platforms, large orgs |

### Free vs Paid System Separation (Critical)
- Free tier: email capture → our system → marketing allowed
- Paid tier: Stripe → our system → financial reporting separate
- These systems NEVER mix

### Revenue Targets
| Year | MRR Target | ARR | Paying Customers | Avg LTV |
|------|-----------|-----|-----------------|---------|
| Y1 | $1,500 | $18K | 100 | $180 |
| Y2 | $15,000 | $180K | 600 | $300 |
| Y3 | $100,000 | $1.2M | 2,000 | $600 |

---

## 6. Customer Acquisition

### Growth Model: Developer-Led + Product-Led Growth (PLG)

**Top of funnel:**
1. Landing page (SEO + direct)
2. SDK pip install (PyPI discovery)
3. API directory listings (RapidAPI, Public APIs)
4. Developer community engagement (LangChain Discord, Reddit, DEV.to)
5. GitHub README + example code

**Conversion:**
- Free tier → Starter ($25): Developer evaluates → hit limit → upgrades
- Starter → Pro ($99): Team grows → API usage increases → upgrades
- Pro → Scale ($349): Productized service launches → volume increases

**Viral loops:**
- Structured output is shareable (entity lists, topic tags) → shown in team dashboards
- YouTube integration (V1.3) → creators share transcripts → signups from content
- Open-source examples on GitHub → copied into new projects

---

## 7. Operations

### Team Structure (Year 1)
| Role | Owner | Status |
|------|-------|--------|
| CEO / Product / Sales | Traves Brady | Active |
| Chief of Staff / Engineering | Aster Vale | Active |
| Marketing / Community | Traves (content) + Aster (systems) | In progress |
| Customer Support | Aster (Year 1), hire at Y2 | Year 2 |
| Legal / Finance | External advisors | As needed |

### Tools & Systems
| Function | Tool | Status |
|----------|------|--------|
| API Server | FastAPI + uvicorn | ✅ Live |
| Job Queue | In-memory → Redis (by Beta) | In progress |
| Database | In-memory → PostgreSQL (by Launch) | Planned |
| SDK | Python (PyPI) | Built, not published |
| Landing Page | Static HTML | Ready for Cloudflare |
| Payments | Stripe | Not wired |
| Email | signalloomai.com alias | Active |
| Status Page | Not yet | Required by Beta |
| Support | hello@signalloomai.com → Front | Required by Beta |

---

## 8. Financial Model

### Startup Costs (To Date)
| Item | Investment |
|------|-----------|
| Mac Studio / compute hardware | ~$16,000 |
| Domain names (signalloomai.com + 4 others) | ~$200 |
| YouTube subscription | $13.99/mo |
| Mission Control card allocation | $4,400 (seed + test) |
| **Total invested** | **~$20,600** |

### Operating Costs (Current — Alpha)
| Item | Monthly |
|------|---------|
| YouTube subscription | $13.99 |
| Cloudflare Pages (free tier) | $0 |
| Domain renewals | ~$5 |
| Stripe fees (3%) | 3% of revenue |
| Compute (local MLX) | $0 (owned hardware) |
| **Total monthly burn** | **~$20/mo** |

### Operating Costs (Launch — Scale Phase)
| Item | Monthly |
|------|---------|
| Cloud compute (MLX burst) | $50-500 |
| Cloudflare (Pro plan) | $20 |
| Stripe fees | 3% of revenue |
| Domain renewals | ~$5 |
| Customer support | $0 (Year 1) |
| Status page | ~$10 |
| **Total monthly burn at 100 customers** | **~$300-800** |

### Gross Margin by Tier
| Tier | Price | Cost/Min (MLX) | Gross Margin |
|------|-------|----------------|------------|
| Free | $0 | $0 (free tier) | N/A |
| Starter | $25 | ~$0.001 | ~95% |
| Pro | $99 | ~$0.0005 | ~97% |
| Scale | $349 | ~$0.0002 | ~98% |

---

## 9. Risk Analysis

### Top 5 Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| OpenAI changes Whisper license | Low | High | Model abstraction layer, CUDA fallback |
| One viral spike + downtime | Medium | High | Pre-scale before public launch, CDN, alerting |
| Key employee burnout (Aster/Traves) | Medium | High | Document systems, build autonomous ops |
| Stripe account suspended | Low | Critical | Clear ToS compliance, proactive Stripe relationship |
| Malicious API abuse (free tier) | Medium | Medium | Credit card gate for free tier (V1.2) |

### Regulatory Risks
- **GDPR (EU):** Need DPA, lawful basis for processing, deletion capability
- **CCPA (California):** Right to delete, do-not-share
- **HIPAA (if medical use):** BAA required before any PHI-adjacent use
- **Export compliance (EAR):** MLX Whisper weights — check Export Administration Regulations

---

## 10. Strategic Priorities (Next 90 Days)

### Immediate (This Week)
1. Cloudflare API token → deploy landing page → public URL live
2. PyPI token → publish Python SDK → `pip install signalloom` live
3. Stripe onboarding → wire paid tier checkout
4. GitHub repo push → community can see code

### Near-Term (30 Days)
5. Free tier email capture → hello@signalloomai.com funnel
6. Product Hunt launch preparation (assets, copy, community seeding)
7. API status page → statuspage.io or self-hosted
8. DELETE /v1/account — data deletion endpoint for CCPA/GDPR

### Medium-Term (60-90 Days)
9. YouTube URL ingest (V1.3) — transcribe from public YouTube links
10. Webhook retry queue — reliability for enterprise-bound customers
11. Speaker diarization (V1.2) — single biggest accuracy/pricing differentiator
12. LangChain tool integration — official LangChain community integration

---

## 11. The 3 Unpopular Truths

1. **The first 90% of the product is the easy part.** The next 10% (reliability, security, docs, support) is what takes 90% of the time. We've built 90%. The next phase is the hard part.

2. **Developer-first products fail when they forget to be products.** Great APIs don't win — great developer experiences do. Documentation, SDK stability, changelogs, and responsiveness in developer communities are the product, not just the API.

3. **The free tier is a business decision, not a generosity decision.** Free users are a marketing funnel, not a cost center. Every free user is a future paying customer or a word-of-mouth marketing asset. Treat them accordingly — with respect, reliability, and a clear upgrade path.

---

## 12. What Success Looks Like

**Year 1 end:**
- 2,000+ API signups
- 100+ paying customers
- $1,500 MRR
- 3 published SDKs (Python ✅, Node.js, Go)
- 1 documented enterprise integration
- Product Hunt launch → top 5 of the day

**Year 2 end:**
- 10,000+ signups
- 500+ paying customers
- $15,000 MRR
- First $100K ARR customer (whitelabel or platform deal)
- SOC 2 Type I completed
- EU data residency deployed

**Year 3 end:**
- $100K MRR
- 2,000 paying customers
- 1M+ audio minutes processed/month
- Series A conversation or sustainable bootstrapped growth
- 2-3 enterprise platform deals

---

*This is a living document. Aster will update this on the first of every month with actuals vs. projections.*
*Last updated: 2026-03-24*
