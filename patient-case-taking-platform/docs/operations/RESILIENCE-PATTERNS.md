# Resilience and Graceful Degradation

All thresholds below are initial hypotheses. Load tests and pilot telemetry must set final values per operation, language, model and facility network.

## Dependency policy

| Dependency | Initial signal | Fallback | Safety boundary |
|---|---|---|---|
| LLM/vLLM | 5-second time-to-first-token target; bounded async deadline by task | Controlled ontology questions, touch entry, queue draft work | Never block signing or deterministic triage; never present an unfinished draft as final |
| Streaming ASR | 3-second chunk-stall signal | Retry a smaller chunk once, then type/tap mode or async transcription | Preserve audio/session reference and explicit pending state |
| PostgreSQL | sustained high latency or connection saturation | Read-only safe cache for eligible views; encrypted local draft for approved kiosk flows | Stop or clearly hold writes when commit status is uncertain; never sign against an unconfirmed write |
| Redis | miss, timeout or restart | Rebuild cache; re-dispatch durable pending jobs from PostgreSQL | Redis loss cannot lose consent, encounter or job truth |
| Elasticsearch | query timeout or unavailable | Direct authoritative timeline/recent-record queries | Search is optional and never an authorization or clinical-truth dependency |
| SMS/WhatsApp provider | timeout or provider error | Queue, alternate approved provider/channel, staff-visible delivery status | No sensitive content in notifications; respect consent and quiet-hours policy |

Use rolling-window circuit breakers, bulkheads for critical versus batch work, bounded retry budgets and full jitter. A circuit opens only after both a minimum request count and an error/timeout threshold; tune from measured traffic rather than hard-coding one global percentage.

## Database and cache behavior

- Route writes, consent/authorization, signing and read-after-write to the PostgreSQL primary. Use replicas for latency-tolerant history/reporting and expose replica lag.
- PgBouncer protects connection limits; every driver and transaction pattern must be tested with the chosen pooling mode.
- L1 in-process cache is limited to non-PHI reference/configuration or tightly bounded process memory. L2 Redis may hold encrypted/minimum-necessary eligible views.
- Stale-while-revalidate applies only to explicitly safe read-only views and always displays the data timestamp. Do not serve stale consent, authorization, alert acknowledgement, or critical allergy/medication data as current.
- Coalesce identical cache misses. Warm reference data and safe aggregates, not broad patient records or the “top facilities” PHI set.
- Offline kiosk capture is an encrypted, expiring, visibly unsynced draft. Sync uses the same idempotency key and requires identity/consent revalidation before record promotion.

## Duplicate and retry control

- API mutation requests carry an idempotency key scoped to actor, operation and resource.
- Database uniqueness and a processed-event ledger provide correctness; a Redis key is only a fast path.
- Retry transient failures at most three times with exponential backoff and full jitter; enforce per-service retry budgets.
- Non-transient validation, authorization and safety failures do not retry.
- Dead-letter replay is audited, rate-limited and uses the original idempotency key.

## Deployment safety

- Default to canary progression such as 5% → 20% → 50% → 100%, gated by error, latency, saturation, clinical workflow and model-quality metrics.
- Use blue/green for high-risk protocol or infrastructure changes where full-environment validation is worth the cost.
- Automate rollback when an approved error/safety threshold persists; “5% for two minutes” is a starting experiment, not a universal rule.
- Use expand/contract database changes and backward-compatible event schemas so old and new pods/consumers coexist safely.
- Feature flags may disable optional behavior, never bypass consent, authorization or safety controls.

## User experience in degraded mode

- Doctor: show a timestamped read-only cached summary only when eligible, with clear pending/stale status; keep manual note entry available.
- Patient/kiosk: show progress and offer touch/text when voice is busy; clearly label unsynced offline drafts.
- Operators: show a stable incident code and recovery action, without provider internals or PHI.

## Verification

Run fault injection only in synthetic-data development/staging environments: worker crashes before offset commit, Redis restart/cold cache, broker lag, PostgreSQL replica lag, dependency latency, partial rollout and object-store denial. Production chaos requires a separately approved safety plan.
