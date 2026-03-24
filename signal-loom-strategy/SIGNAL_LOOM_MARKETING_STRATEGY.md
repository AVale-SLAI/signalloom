# Signal Loom AI — Marketing Strategy
## Right Place, Right Time: Passive, Moderate & Needle-Threading Activities

---

## Our Market Position

Signal Loom AI occupies a specific and defensible niche:
- **Not a consumer transcription tool** (Otter, Descript)
- **Not a pure-play enterprise SaaS** (Gong, Chorus)
- **We are infrastructure for AI systems** — a pipeline component that converts audio/video into structured agent-readable knowledge

This is a developer-first, API-first position. Our marketing must match.

---

## Three-Tier Marketing Strategy

### Tier 1: Basic (Foundation) — Always-On, Low Effort, High Ceiling

These are passive, evergreen activities that compound over time:

| Activity | Description | Cadence | Owner |
|----------|-------------|---------|-------|
| **GitHub README** | Best-in-class README with live examples, benchmark data, and architecture diagrams | Static, update quarterly | Aster |
| **Signal Loom landing page SEO** | Target keywords: "audio to structured JSON API", "transcription for AI agents", "whisper API structured output" | Monthly keyword check | Aster |
| **API Documentation** | OpenAPI spec at `/docs` — serve as the de facto reference | Maintain as product evolves | Aster |
| **Hacker News / Indie Hackers posts** | Organic "I built this" posts when milestones hit | Per milestone | Traves + Aster |
| **Python SDK on PyPI** | First-class pip install experience | Maintain | Aster |
| **Podcast/Webinar appearances** | Traves represents AEHS/Signal Loom on podcasts about AI tools, health tech, bootstrapped businesses | Monthly target | Traves |
| **Email signature** | Traves + Aster team: "Signal Loom — Media In. Machine Intelligence Out." | Always | Traves |
| **LinkedIn** | Traves posts about Signal Loom, AI pipeline, use cases, company building | 2x/week | Traves |
| **Product Hunt launch** | When landing page is live and SDK is published | One-time big push | Traves + Aster |

**Expected output (Year 1):** 500-2,000 signups, 50-200 paying users, $5K-25K MRR

---

### Tier 2: Moderate — Active Community Engagement

These require regular presence but target high-intent communities:

#### 2.1 Developer Community seeding
- **LangChain Discord** — Answer transcription-related questions, link to Signal Loom when relevant (don't spam). Position as "structured output for agent memory"
- **LlamaIndex GitHub** — Open an issue or PR for a Signal Loom reader integration example
- **Hugging Face Spaces** — Deploy a demo transcription Space using our API
- **r/MachineLearning, r/LangChain, r/LocalLLaMA** — Thoughtful comments and posts about structured transcription for AI agents
- **DEV.to, Medium** — Long-form technical posts: "How to build an AI agent with memory using Whisper + Signal Loom"

#### 2.2 Integration-first partnerships
- Target developers building **AI agents, RAG pipelines, voice assistants, and call intelligence tools**
- Approach: contribute code samples, not sales pitches
- Offer: free Scale tier for any developer whose open-source AI tool has 500+ stars

#### 2.3 YouTube content strategy (Signal Loom AI as subject)
- Transcribe our own content library (AEHS has the YouTube subscription)
- Build searchable knowledge base from AEHS video content
- Demonstrate the product by using it internally
- "How we built Signal Loom AI" series = credibility + SEO

#### 2.4 Stripe Atlas / bootstrapped founder communities
- Signal Loom is built for builders — market where bootstrapped founders congregate
- Indie Hackers, Stripe Atlas community, Y Combinator founder network
- Direct comparison to AssemblyAI and Deepgram on price/performance

**Expected output (Year 1-2):** 2,000-10,000 signups, 200-1,000 paying users, $25K-150K MRR

---

### Tier 3: Needle-Threading — High Leverage, Timing Dependent

These are the "right place, right time" activities that require watching for the right moment:

#### 3.1 Hackathon sponsorship (AI/Developer focused)
- Sponsor 1-2 hackathons per year (DEVPOST, Lablab.ai, local AI hackathons)
- Provide Signal Loom API keys + free Scale tier for participants
- Winning projects using Signal Loom get featured on our landing page
- **Timing:** AI hackathon wave happens every Q1 and Q3 — plan ahead

#### 3.2 AI Agent framework integration (LangChain, AutoGen, CrewAI)
- Build and maintain official Signal Loom integrations for major agent frameworks
- When a framework updates and mentions us in release notes = massive organic signal
- **Timing:** As LangChain/LlamaIndex grows, our integration position becomes permanent SEO

#### 3.3 "AI infrastructureIndex" and comparison sites
- Get listed on API directory sites: RapidAPI, API Guru, APIList, Public APIs
- Get reviewed on G2, Capterra (transcription category)
- **Timing:** Once we have 50+ paying users with testimonials

#### 3.4 Enterprise sales (Year 2+)
- Identify companies in TAM use cases (sales call intelligence, legal tech, medical)
- Offer white-label/API partnership — they rebrand, we power the pipeline
- Target: Series A-B startups in these verticals who need transcription infrastructure
- **Timing:** When we have 3-5 case studies and 90+ day retention data

#### 3.5 Press / media (timing dependent)
- "Built with" stories in TechCrunch, The Verge, VentureBeat when a notable AI product launches using Signal Loom
- **Trigger:** When a company with >100K users attributes Signal Loom as part of their stack
- Respond to journalist queries on HARO (Help A Reporter Out) for AI/transcription stories

#### 3.6 Government/Health/Legal vertical SEO
- As we build ISO 13485 / HIPAA-adjacent positioning, target govtech, healthtech, legaltech SEO terms
- "HIPAA-compliant transcription API", "medical dictation pipeline", "legal deposition transcription API"
- **Timing:** Year 2+ when we have compliance documentation to back claims

---

## Competitive Positioning Matrix

| | Signal Loom | AssemblyAI | Deepgram | Otter.ai |
|-|-------------|------------|----------|----------|
| **Price** | MLX-local (free), $25/mo starter | ~$0.05/min | ~$0.01/min + compute | $10-30/seat |
| **Structured output** | Native entities, topics, sentiment | Add-on features | Limited | None |
| **Local processing** | ✅ MLX on Apple Silicon | ❌ Cloud only | ❌ Cloud only | ❌ Cloud only |
| **Agent-ready output** | ✅ Built for AI from day 1 | ❌ | ❌ | ❌ |
| **API-first** | ✅ | ✅ | ✅ | ❌ (consumer) |
| **Free tier** | 100 min/mo | Pay-to-start | Pay-to-start | Limited free |
| **YouTube/URL ingest** | Coming V1.3 | ✅ | ✅ | ✅ |
| **Speaker diarization** | Coming V1.2 | ✅ | ✅ | ✅ |

**Our wedge:** We are the only **developer-first, AI-native, structured-output** transcription API at a price point that doesn't require cloud API costs.

---

## Monthly Marketing Calendar (Minimum Viable)

| Week | Activity |
|------|----------|
| Week 1 | LinkedIn post + GitHub README update |
| Week 2 | DEV.to / Medium technical post |
| Week 3 | Community engagement (LangChain Discord, Reddit) |
| Week 4 | Metrics review + content performance analysis |

---

## What We're NOT Doing (Strategic Trade-offs)

- **Cold outbound sales** — not until Year 2 with case studies
- **Paid ads** — developer/B2B API products don't convert well on LinkedIn/Google ads
- **Consumer marketing** — we are not competing with Otter/Descript
- **Enterprise sales team** — hire only when MRR hits $25K+ and inbound can't keep up
- **Conference sponsorships** — only at $50K+ MRR does this ROI make sense

