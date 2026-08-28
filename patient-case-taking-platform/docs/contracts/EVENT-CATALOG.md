# Event Catalog

## Standard envelope

Every event contains:

- `event_id`
- `event_type`
- `event_version`
- `occurred_at`
- `producer`
- `tenant_or_facility_id`
- `correlation_id`
- `causation_id`
- `aggregate_type`
- `aggregate_id`
- `data_classification`
- `idempotency_key`
- `attempt`
- `artifact_refs`
- `payload`

Do not include raw audio, images, PDFs, unrestricted transcripts, prompts, completions, access tokens or secrets. Use opaque internal artifact IDs; consumers obtain short-lived authorized object access after authorization.

## Initial events

| Event | Producer | Primary consumers |
|---|---|---|
| `PatientRegistered.v1` | Clinical platform | Audit, integration projector |
| `ConsentChanged.v1` | Consent module | ABDM adapter, audit, access cache invalidator |
| `EncounterStarted.v1` | Encounter module | Conversation orchestrator, audit |
| `AnswerConfirmed.v1` | Encounter module | Summary worker, clinical safety evaluator |
| `DocumentUploaded.v1` | Document registry | Malware scan/OCR worker |
| `DocumentProcessingCompleted.v1` | Document worker | Clinical review queue, search projector |
| `ClinicalRecordChanged.v1` | Clinical record module | Summary worker, search projector, ABDM adapter |
| `SummaryRequested.v1` | Clinical platform | Summary worker |
| `SummaryGenerated.v1` | Summary worker | Clinical platform, audit |
| `CriticalAlertRaised.v1` | Alert worker | Clinical inbox, notification policy |
| `NotificationRequested.v1` | Owning workflow | Notification worker |
| `NotificationDeliveryUpdated.v1` | Notification worker | Owning workflow, operations |

## Event backbone

Kafka is the asynchronous backbone from MVP. PostgreSQL stores durable job state and the transactional outbox; Kafka provides transport, isolated consumer groups, bounded replay and dead-letter handling. Select a managed or self-operated Kafka deployment after residency, support, cost and operational review. No producer or consumer may depend on provider-specific behavior without an ADR.

## Topic plan

| Topic | Purpose | Transport retention |
|---|---|---|
| `ai.asr.requested.v1` | Submit asynchronous transcription jobs | 24 hours |
| `ai.asr.completed.v1` | Announce persisted transcript artifact | 7 days |
| `ai.ocr.requested.v1` | Submit document OCR jobs | 24 hours |
| `ai.ocr.completed.v1` | Announce persisted extraction artifact | 7 days |
| `ai.llm.local.requested.v1` | Submit policy-approved local inference job | 24 hours |
| `ai.llm.external.openai.requested.v1` | Submit OpenAI-eligible inference to its isolated pool | 24 hours |
| `ai.llm.external.claude.requested.v1` | Submit Claude-eligible inference to its isolated pool | 24 hours |
| `ai.llm.completed.v1` | Announce normalized persisted result from either path | 7 days |
| `ai.llm.failed.v1` | Announce terminal normalized failure metadata | 7 days |
| `ai.summary.local.requested.v1` | Submit local summary job | 24 hours |
| `ai.summary.external.openai.requested.v1` | Submit OpenAI-eligible summary job | 24 hours |
| `ai.summary.external.claude.requested.v1` | Submit Claude-eligible summary job | 24 hours |
| `ai.summary.completed.v1` | Announce normalized versioned summary draft | 30 days |
| `ai.summary.failed.v1` | Announce terminal summary failure metadata | 30 days |
| `ai.translation.external.openai.requested.v1` | Submit approved OpenAI translation job | 24 hours |
| `ai.translation.external.claude.requested.v1` | Submit approved Claude translation job | 24 hours |
| `clinical.triage.alert-raised.v1` | Announce deterministic red-flag escalation | 90 days, subject to volume and policy |
| `audit.event-recorded.v1` | Transport an audit projection event | 7–30 days; never the compliance archive |

Topic payloads contain metadata and artifact references only. Retention values are planning defaults and require privacy, volume and recovery validation.

## Consumer groups

- `asr-workers` consume ASR requests and publish completed artifact references.
- `ocr-workers` consume OCR requests and publish completed artifact references.
- `llm-local-workers` consume local requests and call only approved vLLM deployments.
- `summary-fast-local-workers` run only the evaluated smaller local summarizer and accept summary tasks within its approved quality envelope.
- `llm-external-openai-workers` and `llm-external-claude-workers` consume their provider-specific topics and have separate credentials, concurrency/token/cost limits and circuit breakers. They must not be separate consumer groups on one shared topic, which would invoke both providers.
- `summary-local-workers` and provider-specific external summary groups fetch authorized inputs by reference.
- `result-normalizers` validate local/external outputs against one schema and publish completed/failed events.
- `triage-engine` evaluates confirmed structured facts and raises deterministic alerts; an LLM is never the sole red-flag detector.
- `audit-projector` writes the immutable audit sink and a time-bounded Elasticsearch projection.

## Delivery rules

- Producers use a transactional outbox.
- Consumers are idempotent using a PostgreSQL processed-event ledger and uniqueness constraints such as `(job_id, stage, model_version)`. Redis may accelerate the check but is not authoritative.
- Schemas are backward compatible within a major version.
- Retries use a maximum of three attempts with exponential backoff and full jitter. Kafka implementations use explicit retry topics or a delayed scheduler rather than blocking partitions.
- Messages that still fail move to a stage-specific dead-letter topic with error class, attempt count and a PHI-safe remediation reference.
- Bloom filters are not used for correctness-sensitive deduplication because false positives could suppress clinical work.
- Events are not used as an undocumented substitute for synchronous authorization checks.
- Each request carries deadline, priority, execution eligibility and estimated token class. Admission control bounds topic age/backlog; Kafka is not an unlimited overflow buffer.
