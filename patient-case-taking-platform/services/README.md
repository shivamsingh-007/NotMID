# Services

- `clinical-platform`: modular transactional core.
- `conversation-orchestrator`: structured multilingual interview sessions.
- `ai-model-gateway`: model routing, credentials, safety and usage controls.
- `llm-runtime-vllm`: private vLLM deployment and approved model versions.
- `speech-service`: AI4Bharat/Bhashini-compatible ASR and Indic TTS routing.
- `clinical-nlp-service`: versioned PyTorch extraction/classification models.
- `rules-service`: deterministic clinician-approved red-flag and policy rules.
- `document-processing-worker`: scan, OCR and extraction pipeline.
- `summary-worker`: source-linked encounter and longitudinal summaries.
- `alert-worker`: deterministic clinical/workflow alerts.
- `notification-worker`: SMS/WhatsApp delivery with consent and deduplication.
- `abdm-adapter`: ABHA/ABDM protocol isolation and reconciliation.

Each service must document owned data, APIs, events, SLOs, privacy classification, failure behavior and operational runbook before implementation.
