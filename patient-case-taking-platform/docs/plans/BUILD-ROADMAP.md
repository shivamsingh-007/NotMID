# Build Roadmap

## Planning assumptions

- Initial pilot: one or two hospitals, Hindi and English, outpatient case-taking.
- AI assists documentation; it does not independently diagnose or prescribe.
- Patients may lack ABHA, smartphones, literacy or reliable connectivity.
- The first release should optimize safe workflow learning, not national-scale infrastructure.

## Approved stack baseline

- Next.js/React/TypeScript monorepo with separate patient, doctor and user-administration deployments.
- FastAPI for the modular clinical core, WebSocket gateway and Python-facing APIs.
- Clerk for staff/patient web authentication, with hospital SSO integration where available and a constrained kiosk pre-auth flow.
- vLLM behind the AI gateway, with HiMed 8B treated as the first candidate rather than a clinically approved model.
- AI4Bharat/Bhashini-compatible ASR, Indic/Bhashini-compatible TTS, an OCR ensemble and PyTorch clinical NLP services.
- Versioned Python rules service for deterministic red flags and policies.
- PostgreSQL for transactional/clinical truth; MongoDB for raw transcript/OCR/model artifacts; Redis for ephemeral state; S3-compatible object storage for binaries.
- WebSockets for interactive updates; Celery + Redis for MVP jobs with durable PostgreSQL state; Kafka/Redpanda after measured scale triggers.
- Elasticsearch for rebuildable document search, audit exploration and operational analytics; optional vector search only after representative evaluation.
- Docker for every deployable; Kubernetes for shared pilot/production. KServe/Ray Serve remain optional later.

## Phase 0 — Discovery, governance and contracts

Duration target: 3–5 weeks.

### Work

- Observe registration, consultation, upload and discharge workflows.
- Define patient, caregiver, receptionist, nurse and doctor journeys.
- Appoint clinical-safety, privacy and data-governance owners.
- Define internal patient identity, duplicate resolution and merge/unmerge rules.
- Validate Clerk privacy, residency, webhook, MFA, session-revocation and hospital-SSO requirements; document the replacement boundary.
- Define kiosk pre-auth capabilities and prove that anonymous sessions cannot search or display PHI.
- Define consent, retention, deletion, emergency access and audit policies.
- Select FHIR resource mappings and ABDM participation roles: HIP, HIU or both.
- Approve the API style, event envelope and service ownership map.
- Define edge route classes, TLS ownership, direct-upload limits and the public-gateway/internal-model-router trust boundary.
- Approve the external-model eligibility matrix by task, facility, purpose, data class, residency and provider contract.
- Benchmark HiMed 8B through vLLM for license compatibility, GPU memory, throughput, Hindi/English quality and clinical-safety baselines.
- Define the queue-to-Kafka migration envelope and measurable triggers: sustained backlog/throughput, replay needs, independent consumer groups or retention beyond Celery operations.
- Benchmark Elasticsearch on multilingual clinical search and filtered vector retrieval; validate licensing, residency, recovery and operating cost rather than adopting vendor headline numbers.
- Establish baseline metrics for consultation and documentation time.

### Exit gate

- Signed clinical workflow and hazard analysis.
- Approved information architecture and threat model.
- Synthetic evaluation set representing Hindi, English and code-switched speech.
- ABDM sandbox path and facility responsibilities confirmed.
- Clerk and hospital-SSO threat model approved, including outage and account-linking recovery.
- HiMed 8B is either approved as a limited candidate for the next phase or replaced based on recorded evaluation evidence.

## Phase 1 — Safe clinical workflow MVP

Duration target: 8–12 weeks.

### Build order

1. Repository tooling, Docker-based local environment, CI checks, secrets handling and contract generation.
2. Next.js application shells plus Clerk integration for patient, doctor and administration audiences.
3. FastAPI token verification, internal identity mapping, facility boundaries and RBAC/ABAC enforcement.
4. Internal patient identity, safe kiosk pre-auth and assisted registration.
5. PostgreSQL transactional schema, MongoDB artifact collections, object-store registry and cross-store reference rules.
6. Encounter and structured case-taking state machine with WebSocket progress updates.
7. AI gateway and vLLM deployment with an evaluated HiMed 8B configuration and manual fallback.
8. AI4Bharat/Bhashini ASR, patient confirmation and correction workflow.
9. Object upload, malware scanning and initial OCR routing with immutable source retention.
10. PyTorch clinical NLP and versioned deterministic Python red-flag rules.
11. Draft summary with provenance plus clinician correction, sign-off and immutable audit.
12. Celery/Redis workers fed from a PostgreSQL transactional outbox for async document, summary and alert workflows.
13. Direct-to-quarantine object upload plus route-specific NGINX/gateway limits and timeout propagation.

### Defer

- Kafka/Redpanda, Elasticsearch, Kubernetes service mesh and multi-region deployment.
- KServe, Ray Serve and Drools-style rule authoring until measured scale or governance requirements justify them.
- Autonomous diagnosis, prescription or AI-only emergency decisions.
- Full longitudinal reasoning across every available patient document.

### Exit gate

- A supervised consultation completes end-to-end.
- No AI draft enters the signed record without clinician approval.
- Critical symptom test cases meet the clinician-approved recall target.
- FastAPI rejects invalid issuer/audience/expired Clerk tokens and every tested cross-role access attempt.
- The platform remains usable for manual entry when Clerk, vLLM or ASR is unavailable, subject to documented identity safeguards.
- Restore drill, access audit and incident runbook pass.

## Phase 2 — Hospital pilot and asynchronous processing

Duration target: 8–10 weeks.

### Work

- Harden Celery/Redis recovery, idempotency, retry/dead-letter handling and PostgreSQL re-dispatch; load-test the Kafka migration threshold.
- Add OCR/document worker and source-linked extraction review.
- Add deterministic red-flag and workflow alert rules.
- Add patient-friendly summary and multilingual TTS.
- Add SMS reminders containing minimal sensitive information.
- Add offline capture with encrypted local queue and explicit sync state.
- Integrate ABDM sandbox identity/linking/consent flows.
- Add operational dashboards for latency, failures and AI quality.
- Add normalized model results, provider-specific budgets/concurrency bulkheads and approved failure UX; keep external inference disabled until its privacy gate passes.
- Deploy the shared pilot environment on Kubernetes with separate CPU/GPU pools and explicit resource limits.

### Exit gate

- Measurable reduction in doctor documentation time.
- Acceptable ASR and clinical-entity error rates by language and environment.
- Zero unresolved high-severity consent or cross-patient data leaks.
- Queue recovery, duplicate delivery and idempotency exercises pass.

## Phase 3 — Multi-facility scale

Duration target: 12–16 weeks after pilot evidence.

### Work

- Facility-aware data isolation and policy enforcement.
- ABDM production onboarding and HIP/HIU flows.
- HPR/HFR verification where applicable.
- HIS, LIMS and PACS adapters.
- Introduce Elasticsearch for derived clinical-document search, audit exploration and aggregate dashboards.
- Migrate high-volume AI pipelines to Kafka/Redpanda consumer groups when the recorded Phase 2 triggers are met; retain Celery for simple local jobs if operationally useful.
- Split Kafka inference topics and worker pools by local versus approved external execution, with bounded backlog/age, normalized results and provider-specific DLQs.
- Autoscale CPU/GPU workers from queue depth and latency.
- Evaluate KServe or Ray Serve only if the number of models, rollout patterns or GPU scheduling needs exceed the vLLM/Kubernetes deployment.
- Add WhatsApp using explicit opt-in and approved low-PHI templates.
- Implement production disaster recovery and regional failover exercises.

### Exit gate

- Load, failover, privacy and clinical-safety targets pass at projected peak volume.
- Search indexes and summaries can be rebuilt from source systems.
- Kafka replay and idempotency exercises pass if the scale-stage backbone is enabled.
- Facility onboarding is repeatable without code forks.

## Phase 4 — Validated advanced assistance

- Specialty-specific interviews.
- Care-gap suggestions and longitudinal risk signals.
- Retrieval-assisted clinical summaries with statement-level citations.
- De-identified analytics governed by explicit purpose and access controls.
- Locally hosted or federated models when privacy, cost or latency justifies them.

Every advanced feature requires a new hazard analysis, clinical evaluation and rollback plan.

## Cross-phase workstreams

| Workstream | Continuous outputs |
|---|---|
| Clinical safety | Hazard log, test cases, approval evidence, incident review |
| Security/privacy | Threat model, access reviews, key rotation, breach drills |
| Data | Migrations, quality rules, lineage, backup restoration |
| AI/ML | Model cards, evaluation reports, drift and cost monitoring |
| UX | Field research, accessibility tests, comprehension metrics |
| Reliability | SLOs, capacity plans, runbooks, recovery exercises |

## First backlog slices

| Slice | Demonstrable outcome | Dependencies |
|---|---|---|
| S1 | Clinician can securely sign in to a facility | IAM, authorization policy |
| S2 | Operator can register and safely find a patient | MPI, audit |
| S3 | Patient can complete one structured complaint flow | Encounter state machine, patient PWA |
| S4 | Doctor sees the confirmed transcript and unresolved questions | Conversation orchestration, clinician web |
| S5 | Doctor edits and signs a note | Clinical record, provenance, audit |
| S6 | Patient receives a simple approved summary | Signed note, multilingual renderer/TTS |
| S7 | Uploaded prescription becomes a reviewed structured document | Object storage, scanning, OCR worker |
| S8 | ABHA-linked record flow works in sandbox | Consent service, ABDM adapter |
