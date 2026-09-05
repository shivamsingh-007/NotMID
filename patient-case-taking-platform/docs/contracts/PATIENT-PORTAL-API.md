# Patient portal API contract

## Boundary

All record-bearing routes require a verified access token with `role=patient`,
an internal patient UUID in `sub`, a tenant UUID and at least one permitted
facility. Every route derives the patient from that identity. There is no
`patient_id` request parameter.

The local demo can mint a synthetic token only when `ENABLE_DEMO_ROUTES=true`.
That mechanism is for local engineering and must not be enabled in a shared or
clinical environment.

## Endpoints

| Method and path | Result | Safety rule |
|---|---|---|
| `GET /api/v1/patient-portal/me/dashboard` | Counts and recent signed/reviewed items | Self and permitted facilities only |
| `GET /api/v1/patient-portal/me/reports` | Clinician-signed summaries | Never returns drafts or rejected versions |
| `GET /api/v1/patient-portal/me/reports/{id}` | Full signed summary with evidence paths | Inaccessible IDs are returned as not found |
| `GET /api/v1/patient-portal/me/reports/{id}/download` | UTF-8 signed report | Private/no-store; includes signature SHA-256 |
| `GET /api/v1/patient-portal/me/timeline` | Clinician-reviewed document facts | Never returns raw OCR or unreviewed candidates |
| `POST /api/v1/patient-portal/me/consents` | Bounded treatment consent | Patient comes from token |
| `GET /api/v1/patient-portal/me/consents` | Patient's consent versions | Self only |
| `POST /api/v1/patient-portal/me/consents/{id}/revoke` | Revoked consent version | Cannot revoke another patient's consent |
| `POST /api/v1/patient-portal/me/intakes` | Durable confirmed intake decision | Active, matching consent and `Idempotency-Key` required |
| `GET /api/v1/patient-portal/me/documents` | Patient upload states | Self and permitted facilities only |
| `POST /api/v1/patient-portal/me/documents` | Registers an upload | Active treatment consent required |
| `POST /api/v1/patient-portal/me/documents/{id}/upload-session` | Exact-object upload grant | Short-lived quarantine target |
| `POST /api/v1/patient-portal/me/documents/{id}/finalize` | Verifies and queues upload | Size, MIME and checksum are server verified |
| `POST /api/v1/patient-portal/me/documents/{id}/cancel` | Cancels eligible upload | Optimistic version required |
| `POST /api/v1/tts/synthesize` | Deterministic WAV status cue | `mock` only; no external network |

## Intake truth boundary

An accepted or rejected summary draft is stored as the patient's confirmed
submission, not as a signed clinical record. A clinician must assemble the
confirmed context, review evidence, edit as needed and sign through the Phase 8
workflow before it appears in patient reports.

The S2S path is:

`audio capture → ASR result → patient confirmation/edit → mock adaptive dialogue → mock WAV status cue → accepted/rejected intake persistence`

Emergency-rule output interrupts routine questions. The mock dialogue and mock
TTS providers do not diagnose, prescribe, or imply that an emergency service has
been contacted.

## Caching and logging

Patient clinical responses are marked private/no-store. Audit and operational
events contain opaque IDs, action, role, status and error class only; complaint
text, answers, OCR text and report narrative must not enter metadata logs.
