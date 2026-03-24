# Signal Loom AI — Governance, Quality Standards & What We Might Be Forgetting

---

## Quality Audit Standard: The Signal Loom QA Framework

Before every public milestone (SDK publish, landing page launch, paid tier launch), the following audit framework applies:

### Pre-Launch Audit Checklist

#### 🔒 Security (Non-Negotiable)
- [ ] API key auth enforced on all non-public endpoints
- [ ] SSRF protection active on URL-based transcription
- [ ] File size limits enforced before processing begins
- [ ] Job ID uses full UUID (no enumeration)
- [ ] Auth errors return JSON 401, not plain text
- [ ] Rate limit exceeded returns JSON 429 with Retry-After header
- [ ] No hardcoded secrets, keys, or credentials in codebase
- [ ] Stripe webhook signature verified on all events
- [ ] CORS policy is explicit (not wide-open in production)
- [ ] SQL injection vectors eliminated (parameterized queries when Postgres added)
- [ ] Command injection eliminated (parameterized subprocess calls)
- [ ] API keys stored as SHA-256 hashes, never plaintext

#### 🐛 Bug Bounty Scope (Report to Aster immediately)
- Any endpoint returning 500 on valid input
- Any endpoint returning incorrect HTTP status code
- Any schema field mismatch between API response and OpenAPI spec
- Any case where a valid API key is rejected
- Any case where a rate-limited user gets a 401 instead of 429
- Any PII or sensitive data leaking in error messages

#### 📄 Documentation Standards
- [ ] OpenAPI spec at `/openapi.json` is accurate and versioned
- [ ] `/docs` Swagger UI is functional and shows all endpoints
- [ ] Every endpoint has a docstring explaining parameters and responses
- [ ] Landing page has no dead links
- [ ] All "coming soon" features are clearly marked as such
- [ ] SDK examples are copy-paste runnable without modification

#### 🧪 API Contract Tests (run before every deploy)
```
POST /v1/keys → 200 with api_key field
GET /v1/limits (no auth) → 401
GET /v1/limits (valid key) → 200 with tier/daily_limit fields
GET /v1/limits (rate limited key) → 429 with Retry-After header
POST /v1/transcribe (no auth) → 401
POST /v1/transcribe (valid key, no file) → 400
POST /v1/transcribe/sync (valid key, file) → 200 with transcript
GET /v1/status/{fake_id} → 404
GET /v1/result/{incomplete_job} → 202
```

#### 🖥️ Infrastructure Health
- [ ] Server uptime > 99% (measured weekly)
- [ ] P95 transcription latency < 60s for 20-min audio
- [ ] P99 transcription latency < 300s for 20-min audio
- [ ] Job queue depth monitored — alert if > 50 jobs queued
- [ ] Disk usage < 70% on all storage volumes
- [ ] Memory usage < 80% on MLX worker machines

---

## What We Might Be Forgetting

### 1. **Legal: Terms of Service & Privacy Policy are real legal exposure**
- Current terms.html and privacy.html are drafts
- They need to be reviewed by a lawyer before serving 100+ paying customers
- **What's missing:** Limitation of liability, indemnification, export compliance (EAR/ITAR if applicable), DMCA agent registration
- **Who needs to review:** Qualified attorney (ideally one familiar with SaaS + AI API)
- **Timeline:** Before any paid customer onboarding

### 2. **Payment processing: PCI DSS compliance**
- We use Stripe — Stripe handles PCI compliance on their side
- But our landing page/server handling payment events needs to not store card data
- **Action:** Ensure no card numbers, CVVs, or cardholder data touches our servers
- **Status:** Currently clean — Stripe handles everything
- **Risk:** First employee who touches payment data introduces scope

### 3. **Tax compliance for SaaS / API products**
- Digital goods tax varies by jurisdiction (EU VAT, US sales tax, GST)
- **What's missing:** Tax calculation for international customers
- **Quick fix:** Use Stripe Tax to handle automatically (Stripe Tax product)
- **Risk:** Selling to EU customers without VAT registration = back-tax exposure

### 4. **Data retention and deletion ("right to be forgotten")**
- We store transcript JSONs and usage data
- CCPA/GDPR requires deletion capability within 30 days of request
- **What's missing:** No customer data deletion endpoint
- **Quick fix:** Add `DELETE /v1/account` that wipes all user data for a key_id
- **Timeline:** Before any EU or California customer

### 5. **Error budget and incident response**
- No formal incident severity classification
- No post-mortem process for outages
- No error budget policy (e.g., "we can be down 4.38 hours/month at 99.5% SLA")
- **Quick fix:** Define SEV-1 through SEV-4, set on-call rotation, write post-mortem template
- **Status:** Fine for Alpha/Beta, required before Enterprise

### 6. **API versioning strategy**
- We said "additive only, no breaking changes ever" — but how is this enforced technically?
- **What's missing:** No API versioning middleware, no deprecation headers
- **Quick fix:** Add `API-Version` header check, sunset headers when v2 launches
- **Timeline:** Before v2 launch

### 7. **SDK stability and breaking change policy**
- Python SDK is installed from PyPI — once users install 0.1.0, how do we push 0.2.0?
- **What's missing:** No SDK changelog, no deprecation warnings in SDK
- **Quick fix:** Keep changelog in SDK README, use Python `warnings` module for deprecations
- **Timeline:** With each SDK publish

### 8. **Customer support infrastructure**
- No help desk, no support email (just `hello@signalloomai.com` alias)
- No status page — customers have no way to know if we're down or it's their code
- **Quick fix:** hello@signalloomai.com → ticketing system (Halo, Front, or even Groove)
- **Status page:** statuspage.io or self-hosted uptimerobot
- **Timeline:** Before Beta launch

### 9. **Bank account for business**
- Mission Control has a card but no dedicated business bank account
- Stripe payouts go to personal or company account?
- **What's missing:** Separate business checking (Fidelity, Mercury, Andreessen-backed neobanks)
- **Why it matters:** Liability separation, cleaner accounting, investor readiness
- **Timeline:** Before first $10K in revenue

### 10. **Founder equity and vesting (if bringing on co-founders/partners)**
- Signal Loom AI is currently 100% Traves-owned
- No formal equity grants, no 409A valuation, no option pool
- **Risk:** Any cofounder or key employee hired needs a equity framework
- **Timeline:** Before any equity grant

---

## Governance Summary: What to Do and When

| Action | Priority | Timeline |
|--------|----------|----------|
| Lawyer review of Terms/Privacy | 🔴 Critical | Before first paid customer |
| Stripe Tax for EU VAT | 🔴 Critical | Before first EU customer |
| DELETE /v1/account endpoint | 🟡 High | Before Beta launch |
| Incident severity + on-call rotation | 🟡 High | Before 10K users |
| API versioning middleware | 🟡 High | Before v2 launch |
| Support email ticketing system | 🟡 High | Before Beta launch |
| Status page | 🟡 High | Before Beta launch |
| Business checking account | 🟠 Medium | Before $10K MRR |
| SDK changelog + deprecation policy | 🟠 Medium | With each SDK publish |
| Equity/option pool framework | 🟠 Medium | Before equity grants |
| SOC 2 Type I | 🟢 Lower | Before Enterprise tier |

---

## Quality Philosophy: Our Standard

Signal Loom AI's quality bar, as defined by Traves's operating philosophy:

- **Medical/clinical adjacent features** → ISO 13485 / FDA / Health Canada caliber
- **Developer-facing infrastructure** → Enterprise API quality (Stripe, Twilio, Plaid level)
- **Consumer-facing (landing page)** → Top-quartile SaaS marketing site quality
- **Security** → FUD-level adversarial review before any public launch

The test is always: *Would I trust this in a regulated workflow? Would I be proud to show this to a potential enterprise customer on day one?*

If the answer is no — it doesn't ship.
