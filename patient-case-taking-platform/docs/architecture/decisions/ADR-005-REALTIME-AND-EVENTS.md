# ADR-005: Separate Realtime Delivery From Durable Events

## Status

Accepted for planning.

## Decision

Use authenticated WebSockets for partial transcripts, progress and time-sensitive UI updates. Use Kafka protocol events for durable asynchronous workflows. Redpanda is the default local and pilot implementation; production may use managed Kafka or Redpanda without changing event contracts.

## Consequences

- WebSocket messages are disposable delivery hints and never the authoritative clinical state.
- FastAPI/PostgreSQL commits durable workflow changes before the transactional outbox publishes events.
- Kafka/Redpanda payloads carry metadata and object IDs, not raw audio or document bodies.
- Consumers are idempotent and use schema versions, bounded retries and dead-letter handling.
- Interactive ASR uses the streaming path rather than waiting for Kafka round trips.

## Exit criteria

- Reconnect/resume behavior is tested without duplicating confirmed answers.
- Event replay produces the same final projection.
- Broker outage does not prevent manual clinical note entry/signing.
