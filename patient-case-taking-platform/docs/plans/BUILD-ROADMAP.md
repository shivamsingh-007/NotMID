# Build Roadmap

## Planning assumptions

- Initial pilot: one or two hospitals, Hindi and English, outpatient case-taking.
- AI assists documentation; it does not independently diagnose or prescribe.
- Patients may lack ABHA, smartphones, literacy or reliable connectivity.
- The first release should optimize safe workflow learning, not national-scale infrastructure.

## Phase 0 — Discovery, governance and contracts

Duration target: 3–5 weeks.

### Work

- Observe registration, consultation, upload and discharge workflows.
- Define patient, caregiver, receptionist, nurse and doctor journeys.
- Appoint clinical-safety, privacy and data-governance owners.
- Define internal patient identity, duplicate resolution and merge/unmerge rules.
- Define consent, retention, deletion, emergency access and audit policies.
- Select FHIR resource mappings and ABDM participation roles: HIP, HIU or both.
- Approve the API style, event envelope and service ownership map.
- Establish baseline metrics for consultation and documentation time.

### Exit gate

- Signed clinical workflow and hazard analysis.
- Approved information architecture and threat model.
- Synthetic evaluation set representing Hindi, English and code-switched speech.
- ABDM sandbox path and facility responsibilities confirmed.

## Phase 1 — Safe clinical workflow MVP

Duration target: 8–12 weeks.

### Build order

1. Repository tooling, CI checks, secrets handling and local development environment.
2. Workforce identity, facility boundaries and RBAC.
3. Internal patient identity and assisted registration.
4. Encounter and structured case-taking state machine.
5. Patient PWA, assisted kiosk and clinician review views.
6. Object upload with malware scanning and immutable source retention.
7. AI gateway with Hindi/English ASR, transcription confidence and provider isolation.
8. Patient confirmation and correction workflow.
9. Draft encounter summary with source provenance.
10. Clinician correction, sign-off and immutable audit trail.

### Defer

- MongoDB, OpenSearch, Kubernetes service mesh and multi-region deployment.
- Autonomous diagnosis, prescription or AI-only emergency decisions.
- Full longitudinal reasoning across every available patient document.

### Exit gate

- A supervised consultation completes end-to-end.
- No AI draft enters the signed record without clinician approval.
- Critical symptom test cases meet the clinician-approved recall target.
- Restore drill, access audit and incident runbook pass.

## Phase 2 — Hospital pilot and asynchronous processing

Duration target: 8–10 weeks.

### Work

- Introduce Kafka with outbox, schema registry, retries and dead-letter handling.
- Add OCR/document worker and source-linked extraction review.
- Add deterministic red-flag and workflow alert rules.
- Add patient-friendly summary and multilingual TTS.
- Add SMS reminders containing minimal sensitive information.
- Add offline capture with encrypted local queue and explicit sync state.
- Integrate ABDM sandbox identity/linking/consent flows.
- Add operational dashboards for latency, failures and AI quality.

### Exit gate

- Measurable reduction in doctor documentation time.
- Acceptable ASR and clinical-entity error rates by language and environment.
- Zero unresolved high-severity consent or cross-patient data leaks.
- Kafka replay and idempotency exercises pass.

## Phase 3 — Multi-facility scale

Duration target: 12–16 weeks after pilot evidence.

### Work

- Facility-aware data isolation and policy enforcement.
- ABDM production onboarding and HIP/HIU flows.
- HPR/HFR verification where applicable.
- HIS, LIMS and PACS adapters.
- Introduce OpenSearch for derived clinical search.
- Autoscale CPU/GPU workers from queue depth and latency.
- Add WhatsApp using explicit opt-in and approved low-PHI templates.
- Implement production disaster recovery and regional failover exercises.

### Exit gate

- Load, failover, privacy and clinical-safety targets pass at projected peak volume.
- Search indexes and summaries can be rebuilt from source systems.
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

