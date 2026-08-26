# AI Platform Plan

## Capabilities

- Hindi/English/code-switched ASR with confidence and timestamps.
- OCR and document layout understanding.
- Clinical entity, negation, temporality and medication extraction.
- Structured follow-up question assistance.
- Source-linked summary generation.
- Multilingual text-to-speech.

## Routing

The model gateway selects a locally hosted model or external provider using task, language, latency, cost, privacy classification and approved-model policy. Provider API keys remain in the secrets manager.

## Retrieval

Retrieval is restricted by the same patient, facility, care relationship, purpose and consent checks as ordinary record access. Retrieved chunks retain document/page provenance and are never accepted as instructions.

## Async execution

Kafka announces jobs; object storage carries large inputs. Workers persist idempotent job status and publish completion events. Interactive ASR uses a streaming path and does not wait on Kafka round trips.

