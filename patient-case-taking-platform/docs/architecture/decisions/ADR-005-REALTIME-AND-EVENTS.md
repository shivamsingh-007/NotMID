# ADR-005: Separate Realtime Delivery From Durable Events

## Status

Accepted for planning.

## Decision

Use authenticated WebSockets for partial transcripts, progress and time-sensitive UI updates. Use Celery with Redis for MVP background work, while PostgreSQL retains durable workflow/job state and a transactional outbox. Adopt Kafka or Redpanda when measured replay, throughput, fan-out or independent-consumer requirements justify it. Both stages use the same versioned, reference-only job envelope.

## Consequences

- WebSocket messages are disposable delivery hints and never the authoritative clinical state.
- FastAPI/PostgreSQL commits durable workflow changes before the transactional outbox publishes events.
- Queue/broker payloads carry metadata and internal artifact IDs, not raw audio, unrestricted transcripts, prompts, completions or document bodies.
- Consumers are idempotent and use schema versions, bounded retries and dead-letter handling.
- PostgreSQL unique constraints and a processed-event ledger provide correctness; Redis keys may accelerate checks but are not the idempotency source of truth.
- Interactive ASR uses the streaming path rather than waiting for queue round trips.

## Exit criteria

- Reconnect/resume behavior is tested without duplicating confirmed answers.
- Retried or replayed jobs produce the same final projection.
- Broker outage does not prevent manual clinical note entry/signing.
