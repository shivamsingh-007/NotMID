# System Architecture

## Architectural style

Use a modular clinical core plus isolated asynchronous and integration services.

The core initially owns patient identity, consent, encounters and signed records in one deployable application with strict internal module boundaries. This avoids premature distributed transactions while workflows are still changing.

Separate services are justified when they have materially different scaling, security or availability needs:

- conversation orchestration: streaming and session state;
- AI model gateway: provider credentials, policy enforcement and GPU/model routing;
- document worker: CPU/GPU-heavy asynchronous processing;
- summary and alert workers: event-triggered computation;
- notification worker: third-party delivery and retry isolation;
- ABDM adapter: external protocol, credentials and callback isolation.

## Edge request path

`Client → WAF/DDoS → managed load balancer → API gateway → channel BFF/core API`

- CDN serves static public assets only.
- Authenticated clinical responses must use private/no-store caching rules.
- The API gateway handles authentication validation, request limits, routing and correlation IDs.
- Rate limits differ for human interactive, file upload, integration callback and internal worker traffic.
- Nginx is optional ingress infrastructure, not an additional business gateway.

## Core modules

| Module | Owns | Does not own |
|---|---|---|
| Patient identity | Internal patient ID, demographics, duplicates, merges, external IDs | ABDM credentials or clinical notes |
| Consent | Purpose, scope, expiry, delegation, revocation, emergency access evidence | Authentication credentials |
| Encounter | Case-taking state, confirmed answers, encounter lifecycle | Model-provider logic |
| Clinical record | Signed notes, allergies, medications, observations, provenance | Search indexes |
| Document registry | Document metadata, patient/encounter association, processing status | Binary content |
| Audit | Actor, action, purpose, target, time and outcome | Ordinary application logs |

## Conversation boundary

The conversation orchestrator is a deterministic workflow controller assisted by models. The LLM must not control authorization, consent, emergency escalation or record signing.

Pipeline:

`audio → voice activity detection → language identification → ASR → normalization → clinical entity extraction → workflow decision → safety validation → response text → TTS`

Each produced assertion stores:

- source utterance or document reference;
- speaker and capture time;
- model/prompt version;
- confidence;
- patient correction/confirmation;
- clinician correction/acceptance.

## Availability classes

| Capability | Target behavior |
|---|---|
| Registration and record view | Highly available; graceful degradation without AI |
| Clinician note/signing | Must remain available during Kafka or model-provider outage |
| Live transcription | Degrade to manual text entry |
| OCR and summary generation | Async, retryable, visible pending state |
| Notifications | Async, at-least-once with deduplication |
| Search | Optional derived capability; direct patient timeline remains available |
| ABDM exchange | Async/callback-aware with reconciliation |

## Initial deployment

- Managed PostgreSQL with encryption, point-in-time recovery and tested restore.
- Versioned encrypted object storage with malware quarantine.
- Redis for ephemeral session/cache/rate-limit state only.
- Kafka introduced in Phase 2, with three brokers or managed equivalent for production.
- OpenSearch introduced only when longitudinal search is required.
- CPU and GPU worker pools scaled independently.
- Central OpenTelemetry-compatible metrics, logs and traces with PHI redaction.
- Secrets manager/KMS; no secrets in source or static environment files.

