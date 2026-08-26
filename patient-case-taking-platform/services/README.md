# Services

- `clinical-platform`: modular transactional core.
- `conversation-orchestrator`: structured multilingual interview sessions.
- `ai-model-gateway`: model routing, credentials, safety and usage controls.
- `document-processing-worker`: scan, OCR and extraction pipeline.
- `summary-worker`: source-linked encounter and longitudinal summaries.
- `alert-worker`: deterministic clinical/workflow alerts.
- `notification-worker`: SMS/WhatsApp delivery with consent and deduplication.
- `abdm-adapter`: ABHA/ABDM protocol isolation and reconciliation.

Each service must document owned data, APIs, events, SLOs, privacy classification, failure behavior and operational runbook before implementation.

