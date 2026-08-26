# ADR-002: Minimize Authoritative Data Stores

## Status

Proposed.

## Decision

Use PostgreSQL as the transactional source of truth, object storage for binary sources, Redis for ephemeral state and OpenSearch only for derived search. Do not introduce MongoDB in the initial architecture.

## Consequences

- Fewer consistency and operational failure modes.
- FHIR and flexible document metadata can use JSONB initially.
- OpenSearch and vector indexes must be rebuildable.
- MongoDB requires a later ADR backed by measured workload evidence.

