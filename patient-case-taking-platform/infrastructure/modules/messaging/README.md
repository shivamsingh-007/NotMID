# Messaging Module

MVP: Celery with Redis transport, PostgreSQL durable job state/outbox, bounded retries and dead-letter inspection. Scale stage: Kafka-compatible messaging through managed Kafka or Redpanda, schema registry, retry/dead-letter topics, replay tooling and lag monitoring. Both use the versioned reference-only envelope in `docs/contracts/EVENT-CATALOG.md`.
