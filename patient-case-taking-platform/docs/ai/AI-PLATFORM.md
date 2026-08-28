# AI Platform Plan

## Capabilities

- Hindi/English/code-switched ASR with confidence and timestamps.
- OCR and document layout understanding.
- Clinical entity, negation, temporality and medication extraction.
- Structured follow-up question assistance.
- Source-linked summary generation.
- Multilingual text-to-speech.

## Serving topology

- The conversation orchestrator and workers call the AI model gateway, never vLLM or external model providers directly.
- The gateway exposes task-level APIs, enforces minimum-necessary context, attaches model/prompt versions and routes approved requests to vLLM.
- vLLM exposes an internal OpenAI-compatible endpoint and initially serves HiMed 8B as a candidate model.
- HiMed 8B is not a clinical endorsement: licensing, provenance, Hindi/English performance, hallucination, omission, red-flag recall, latency and GPU-memory results must pass the clinical release gate.
- If the candidate fails, the gateway preserves the interface while another evaluated model replaces it.

## Routing

The model gateway selects a vLLM-hosted or approved external model using task, language, latency, cost, privacy classification and approved-model policy. Provider API keys remain in the secrets manager. Model names supplied by clients are ignored; routing is controlled by server policy.

## Speech, OCR and clinical NLP

- Route ASR by detected language and acoustic conditions to approved AI4Bharat/Bhashini-compatible models. Preserve word/segment timing, confidence and language/code-switch metadata.
- Use Indic/Bhashini-compatible TTS only for approved patient-facing text; never speak an unreviewed diagnosis or prescription as authoritative.
- Route printed documents through PaddleOCR/Tesseract baselines and use TrOCR/Donut or a Hindi handwriting specialist only when document classification warrants it.
- Store page and bounding-region provenance for every OCR value. Low-confidence or conflicting values enter a human review queue.
- Run clinical entity, negation, temporality and classification models as versioned PyTorch services.

## Deterministic rules

Start with a versioned Python rules service whose inputs and outputs are explicit schemas. Rules are clinician-owned, testable and evaluated before release. Consider a Drools-style engine later only if non-developers must author complex policies and the added operational/runtime boundary is justified.

## Retrieval

Retrieval is restricted by the same patient, facility, care relationship, purpose and consent checks as ordinary record access. Retrieved chunks retain document/page provenance and are never accepted as instructions.

## Async execution

For the MVP, Celery workers consume Redis-queued jobs while PostgreSQL retains durable job/workflow state, the transactional outbox and stable artifact references. Object storage carries large inputs and MongoDB carries versioned raw/intermediate JSON artifacts. At measured scale, Kafka/Redpanda consumer groups replace the queue transport without changing the reference-only envelope. Workers persist idempotent status and result references before announcing completion. Interactive ASR and WebSocket updates use a streaming path and do not wait on async queue round trips.

## Model operations progression

1. MVP: Dockerized vLLM and dedicated PyTorch services with fixed approved versions.
2. Pilot: Kubernetes deployments, GPU node pools, health probes, canary rollout and autoscaling from queue/latency metrics.
3. Scale: evaluate KServe or Ray Serve only when multi-model routing, rollout automation or distributed inference requirements cannot be met cleanly by the existing gateway plus Kubernetes.
