# Traffic Control and Model Routing

## Request path

```text
Client
  → CDN/WAF/DDoS protection
  → managed load balancer
  → NGINX ingress
  → public API gateway
  → channel BFF / FastAPI clinical platform
  → internal AI model router
  → local vLLM or approved external-provider worker pool
```

The public API gateway and internal AI model router are separate trust boundaries. The gateway must never let a client choose an arbitrary model or external provider.

## Responsibility matrix

| Layer | Responsibilities | Must not do |
|---|---|---|
| CDN/WAF/load balancer | DDoS protection, public static assets, health-aware distribution, optional public TLS termination | Cache authenticated clinical responses |
| NGINX ingress | TLS termination or re-encrypted ingress, request/body/header limits, coarse IP/device/facility throttles, route classes | Make clinical authorization or provider-selection decisions |
| Public API gateway | Clerk token validation, API quotas, request shaping, correlation IDs, timeout budget propagation and route policy | Treat gateway auth as sufficient clinical authorization; hold large document bodies |
| FastAPI/core | Authoritative facility/care/consent authorization, validation, database-backed idempotency and workflow commit | Call unapproved model endpoints directly |
| Internal AI model router | Approved task/model/provider policy, local capacity admission, privacy classification, token/cost budgets and result contract | Accept client-selected providers or silently export PHI |
| Async transport | Celery/Redis for MVP; Kafka/Redpanda at scale for bounded queued work, replay and DLQ | Become clinical truth or an unlimited overflow buffer |
| Worker pools | Isolated local inference, external-provider calls and normalization | Share provider credentials or concurrency pools across trust classes |

Cloud deployments may terminate public TLS at the managed load balancer, then re-encrypt or use mTLS to NGINX. Single-site deployments may terminate at NGINX. The selected topology must document certificate ownership and hop-by-hop encryption.

## Upload path

1. The client requests an upload intent from FastAPI.
2. FastAPI authorizes patient/encounter/facility scope and creates a pending `document_registry` record.
3. The client uploads directly to a quarantined object-storage location using a short-lived, size/type-constrained signed request.
4. Object completion triggers checksum validation, malware scanning and document processing.
5. Only validated objects are promoted to the clinical prefix and made available to authorized workers.

NGINX retains conservative body limits for API payloads and small fallback uploads. Large medical files do not traverse API pods. Limits are defined per route, not one global value.

## Model-routing decision

The router evaluates, in order:

1. task is approved for AI and the requested output is non-authoritative;
2. data classification permits the candidate execution location;
3. facility/provider contract, residency, consent and purpose permit external processing;
4. local capacity, deadline and expected token demand;
5. provider allowlist, health, concurrency, daily/monthly token and cost budgets;
6. model/language quality policy and required normalized schema version.

If external processing is not explicitly permitted, local saturation produces a delayed/manual fallback—not automatic data export. Provider API keys remain in a secrets manager and are available only to that provider's isolated worker pool.

## Admission control and priority

- Reserve capacity for clinician-facing summaries and safety-adjacent workflows; batch translation and reprocessing use lower-priority pools.
- Every job carries a deadline, priority, estimated token class and maximum attempts.
- Define maximum queue age and backlog per task/facility. On limit breach, defer or reject optional work with a stable status instead of growing an unbounded queue.
- Kafka absorbs bounded bursts and enables replay; it is not permission to accept more work than downstream retention, privacy and latency budgets support.
- External workers have provider-specific token buckets, concurrency semaphores and retry budgets. Local and external pools never share a bulkhead.

## Normalized result contract

All providers return the same internal envelope:

- `job_id`, `request_id`, `task_type` and `schema_version`;
- provider, model, model version and execution location;
- prompt-template and policy versions;
- input/output artifact IDs and content hashes;
- structured output, confidence/validation status and provenance references;
- token usage, latency, finish reason and normalized error class;
- timestamps, attempt and redaction decision.

Kafka and ordinary logs contain metadata and opaque artifact IDs, never full prompts or responses. When raw prompt/response retention is approved, encrypted artifacts use minimum-necessary content, short policy-controlled retention and audited access. Audit evidence records hashes, versions, redaction decisions and outcomes rather than unrestricted content.

## Failure behavior

| Audience | Safe response |
|---|---|
| Patient | “Your information is being processed. Please continue with the next step.” Offer touch/text when the blocked task is interactive. |
| Doctor | “AI summary delayed — showing structured intake and extracted records.” Keep edit-first and signing workflows available. |
| Operations | Provider, approved model identifier, normalized status/error class, latency, attempt, queue depth/age, budget state and correlation ID; no PHI or raw provider body. |

If local and external inference both fail, show confirmed slot-filled intake, document timeline and reviewable raw extractions; enable physician edit-first workflow; create one bounded background-regeneration job only when it is still useful before its deadline.

## Implementation slices

### T1 — Define edge route classes

**Acceptance criteria:** Route-specific body, timeout and coarse rate-limit policies exist for interactive APIs, WebSockets, upload intents, callbacks and operations; authenticated responses are `private, no-store`; TLS ownership is documented.

**Verification:** Configuration tests reject oversized/invalid requests, preserve correlation IDs and keep WebSocket upgrades working.

**Dependencies:** Edge hosting decision.

### T2 — Implement direct document upload

**Acceptance criteria:** Authorized upload intent creates a pending registry row; signed upload is constrained by object key, size, type and expiry; only scanned/checksummed objects are promoted.

**Verification:** End-to-end tests cover expired URLs, oversize files, checksum mismatch, malware quarantine and cross-patient denial.

**Dependencies:** T1, document registry and object storage.

### T3 — Define model policy and normalized contracts

**Acceptance criteria:** Clients cannot select providers; every task has data-classification and external-processing policy; local/external outputs validate against one versioned result schema.

**Verification:** Contract tests cover both execution paths and reject schema/provider-policy violations.

**Dependencies:** AI gateway, privacy review and model evaluation.

### T4 — Add provider budgets and isolated pools

**Acceptance criteria:** Each provider has concurrency, token, cost, retry and circuit-breaker limits; local/external workers use separate credentials and bulkheads; limits generate PHI-safe telemetry.

**Verification:** Load tests prove one saturated or failing provider cannot exhaust the local pool or another provider's budget.

**Dependencies:** T3 and secrets manager.

### T5 — Add scale-stage Kafka routing

**Acceptance criteria:** Local/external request topics, normalized result/failure topics, retry tiers and DLQs use the common envelope; queue age/backlog admission limits are enforced; replay is idempotent.

**Verification:** Replay, duplicate, poison-message, saturated-GPU and external-rate-limit drills preserve one logical result per job.

**Dependencies:** T3–T4 and recorded Kafka migration trigger.

### Checkpoint

- Manual clinical workflows pass with local and external inference disabled.
- No raw prompt, response, token or document appears in Kafka, logs or metrics.
- Patient, doctor and operations failure messages match the approved UX and incident policy.
- Cost, latency, queue age and provider-health dashboards can explain every routing decision by correlation ID.
