# System Architecture

## Architectural style

Use a modular clinical core plus isolated asynchronous and integration services.

The core is a FastAPI application that initially owns patient identity, consent, encounters and signed records in one deployable application with strict internal module boundaries. This avoids premature distributed transactions while workflows are still changing.

Separate services are justified when they have materially different scaling, security or availability needs:

- conversation orchestration: streaming and session state;
- AI model gateway: vLLM/provider credentials, policy enforcement and GPU/model routing;
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

## Concrete technology choices

| Layer | Selected approach | Boundary |
|---|---|---|
| Web channels | Next.js/React TypeScript monorepo with PWA support | Separate patient, doctor and user-admin deployments share packages, not routes or feature state |
| API layer | FastAPI with Pydantic/OpenAPI | Modular clinical core plus independently scalable workers/adapters |
| Identity | Clerk for staff and patient web authentication; hospital SSO through supported OIDC/SAML integration | FastAPI verifies issuer, audience, signature and expiry, then applies internal facility/care/consent authorization |
| Realtime | WebSockets | Interactive transcript/status updates only; reconnect and authorization are explicit |
| Durable events | Kafka protocol; Redpanda default for local/pilot, managed Kafka or Redpanda for production | Transactional outbox, schema registry, idempotency, retries and dead letters |
| LLM | AI gateway to vLLM serving HiMed 8B as the initial candidate | Model is not approved until license, privacy, language, safety and hardware evaluations pass |
| ASR/TTS | AI4Bharat/Bhashini-compatible ASR and Indic/Bhashini-compatible TTS | Stream through dedicated speech services; preserve confidence, timing and language metadata |
| OCR | Routed ensemble of PaddleOCR/Tesseract plus TrOCR/Donut and a Hindi handwriting specialist | Original documents remain immutable; every extraction retains page/region provenance |
| Clinical NLP | PyTorch inference services | Versioned entity, negation, temporality and classification outputs |
| Rules | Versioned Python rules service first | Deterministic urgent-symptom and policy rules; consider Drools only for demonstrated authoring needs |
| Data | PostgreSQL + MongoDB + Redis + S3-compatible object storage + OpenSearch | Store ownership is defined in `DATA-OWNERSHIP.md` |
| Runtime | Docker everywhere; Kubernetes for shared pilot/production environments | KServe/Ray Serve deferred until model count or traffic warrants another control plane |

## Authentication and authorization flow

1. Clerk authenticates staff or patient web sessions and issues a short-lived token for the correct application audience.
2. FastAPI validates the token against pinned Clerk JWKS metadata and maps `clerk_user_id` to an internal workforce, patient or caregiver identity.
3. The authorization layer evaluates role, facility, care relationship, consent, purpose and record sensitivity on every request.
4. Hospital SSO identities are linked to the same internal identity model; Clerk is replaceable at the adapter boundary.
5. Kiosk pre-auth may create only an opaque, expiring intake session. It cannot search records or display PHI until the patient or an attributed operator completes identity verification.

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

WebSockets carry partial transcript and job-status updates. Durable workflow changes are written through FastAPI/PostgreSQL and emitted through the outbox to Kafka/Redpanda. Interactive audio is not routed through Kafka.

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

- Next.js applications and FastAPI services packaged as Docker images.
- Docker Compose for local development; Kubernetes for shared pilot and production environments.
- Managed PostgreSQL with encryption, point-in-time recovery and tested restore.
- Managed MongoDB or an equivalently operated replica set for raw transcript/OCR/model artifacts, with PHI-aware retention and restore tests.
- Versioned encrypted object storage with malware quarantine.
- Redis for ephemeral session/cache/rate-limit state only.
- Redpanda provides the Kafka-compatible local/pilot backbone; production may use managed Kafka or Redpanda without changing contracts.
- OpenSearch introduced only when longitudinal search is required.
- vLLM and other GPU services run in independently scalable GPU pools; CPU workers scale from queue depth.
- KServe or Ray Serve is an optional later control plane, not an MVP dependency.
- Central OpenTelemetry-compatible metrics, logs and traces with PHI redaction.
- Secrets manager/KMS; no secrets in source or static environment files.
