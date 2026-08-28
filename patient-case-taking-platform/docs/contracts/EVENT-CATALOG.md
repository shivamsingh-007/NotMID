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
- `payload`

Do not include raw audio, images, PDFs, unrestricted transcripts, access tokens or secrets. Use short-lived authorized object references or internal object IDs.

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

Use Kafka protocol contracts. Redpanda is the default local and pilot implementation; production may use managed Kafka or Redpanda after residency, support, cost and operational review. No producer or consumer may depend on vendor-specific behavior without an ADR.

## Delivery rules

- Producers use a transactional outbox.
- Consumers are idempotent by `event_id`.
- Schemas are backward compatible within a major version.
- Retries use bounded exponential backoff.
- Poison messages move to a dead-letter topic with a remediation runbook.
- Events are not used as an undocumented substitute for synchronous authorization checks.
