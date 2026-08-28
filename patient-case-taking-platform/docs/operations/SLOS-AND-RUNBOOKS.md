# Reliability Plan

## Initial service objectives

Final targets require pilot traffic measurements. Start by defining and measuring:

- availability of registration, record view and clinician signing;
- p95 interactive API latency;
- p95 partial and final transcription latency;
- asynchronous document/summary completion time;
- notification delivery latency and duplicate rate;
- ABDM callback completion and reconciliation backlog;
- recovery point and recovery time for clinical records and documents.

## Required runbooks

- Database restore and point-in-time recovery.
- Object-store recovery and accidental access exposure.
- Kafka outage/outbox recovery, lag, poison message, dead-letter remediation and replay.
- HiMed/fast-local/OpenAI/Claude routing failure and provider-budget exhaustion.
- Elasticsearch outage, failed projection and full rebuild.
- AI provider outage or unsafe-output spike.
- ABDM credential/callback failure.
- Notification provider outage.
- Patient identity merge incident.
- PHI exposure or suspected breach.
- Regional/facility outage and manual downtime workflow.

## Observability rules

- Use correlation IDs from edge through events and workers.
- Metrics use low-cardinality identifiers and never patient names/ABHA numbers.
- Traces exclude request/response bodies containing clinical data.
- Security audit is separate from debugging logs.
- Alert on user-visible symptoms and safety risks, not only CPU utilization.

Detailed dependency fallbacks, cache behavior, rollout controls and fault-injection cases are defined in `RESILIENCE-PATTERNS.md`.
