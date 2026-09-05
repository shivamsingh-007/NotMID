# MediKiosk Setup and Usage Guide

This guide is for developers, designers and reviewers starting MediKiosk on a new device. The recommended path uses Docker Compose and works on Windows, macOS and Linux.

> **Prototype notice:** the current dashboards use synthetic demonstration content. Do not enter real patient information. AI-assisted text is a draft and is not a diagnosis, prescription or signed medical record.

## 1. What starts locally

| Service | Address | Purpose |
|---|---|---|
| Patient experience | <http://localhost:3000> | Bilingual intake, consent, uploads and signed reports |
| Nurse dashboard | <http://localhost:3001> | Triage, vitals, alerts and handoffs |
| Doctor dashboard | <http://localhost:3001/doctor> | Evidence review, editing and sign-off |
| Document review | <http://localhost:3001/documents/review> | Source-adjacent prescription candidate review |
| Admin console | <http://localhost:3002> | Workforce and facility administration scaffold |
| API | <http://localhost:8000> | FastAPI application |
| API documentation | <http://localhost:8000/docs> | Interactive development API reference |
| MinIO console | <http://localhost:9002> | Local object-storage administration |

PostgreSQL, MongoDB, Redis, Kafka and MinIO also run locally through Docker. Their data persists in named Docker volumes.

## 2. Prerequisites

### Recommended Docker setup

- Git 2.40 or newer
- Docker Desktop on Windows/macOS, or Docker Engine with the Compose plugin on Linux
- At least 8 GB RAM available to Docker
- Ports `3000`, `3001`, `3002`, `5432`, `6379`, `8000`, `9000`, `9002`, `9092` and `27017` available

Verify the tools:

```bash
git --version
docker --version
docker compose version
```

### Frontend-only development

Install Node.js 22 LTS and npm 10 or newer. Python is not required when working only on the synthetic dashboard UI.

### Backend development outside Docker

Install Python 3.11 or newer. Docker is still the simplest way to run PostgreSQL, MongoDB, Redis, Kafka and MinIO.

## 3. Clone and configure

```bash
git clone https://github.com/shivamsingh-007/NotMID.git
cd NotMID/patient-case-taking-platform
```

Create the local environment file.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

The checked-in values are local-only placeholders. Never reuse them for a shared, pilot or production environment. Clerk keys may remain empty for the current local prototype.

For the complete local demo, including Phase 5 assisted questions and the
Phase 7 document APIs, edit `.env` and set:

```dotenv
ENABLE_DEMO_ROUTES=true
DOCUMENT_WORKFLOW_ENABLED=true
SUMMARY_WORKFLOW_ENABLED=true
LLM_PROVIDER=mock
OCR_PROVIDER=paddleocr_fast
TTS_PROVIDER=mock
DOCUMENT_OCR_AUTOMATION_ENABLED=true
DOCUMENT_EXTRACTION_AUTOMATION_ENABLED=true
```

`mock` is the only supported clinical dialogue/summary provider. The local
stack does **not** start vLLM, download HiMed weights, require a GPU, ask for an
OpenAI/Claude key, or send patient text to an external model API. A different
`LLM_PROVIDER` value makes the Phase 8 API fail closed.
The document worker uses the real CPU PP-OCRv5 mobile detector and recognizer. On its first start it
downloads official PaddleOCR model artifacts into named Docker cache volumes;
no API key is required. `OCR_PROVIDER=mock` remains available only for isolated
development/tests. Real inference is still engineering evidence, not clinical
accuracy validation. The local mock TTS WAV cue is contract scaffolding, not
production speech.

## 4. Start everything with Docker

Build and start the complete local stack:

```bash
docker compose up --build
```

The first build downloads images and installs dependencies, so it can take several minutes. Compose applies migrations before starting the API and workers. Wait until the API, three Next.js services, ClamAV and document workers report ready/running.

Run in the background instead:

```bash
docker compose up --build -d
docker compose ps
```

Verify the API:

```bash
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
```

PowerShell alternative:

```powershell
Invoke-RestMethod http://localhost:8000/healthz
Invoke-RestMethod http://localhost:8000/readyz
```

Open the dashboard URLs from the table in section 1.

The Compose topology intentionally has no vLLM service. Dialogue and summaries
use the mock provider, the document worker uses real PP-OCRv5, and TTS returns a
local deterministic WAV cue. PP-OCRv5 downloads its public weights on first use;
no component needs a hosted inference API or API key.

To verify the mock clinical assistant after enabling demo routes:

```bash
curl http://localhost:8000/api/v1/clinical-ai/health
```

The response should report `"provider":"mock"`, `"ready":true` and `"external_network_used":false`. Then open <http://localhost:3000/case-taking/assisted>.

Verify the actual OCR model after the first worker build/download:

```bash
docker compose run --rm --no-deps document-ocr-worker python -m tools.verify_real_ocr
```

The command must print `PASS provider=paddleocr_fast model=PP-OCRv5-mobile`. It creates
only a synthetic printed image in memory; it does not use a patient document.

To exercise the Phase 6 Slice 6.1 contract with synthetic data:

```bash
curl -X POST http://localhost:8000/api/v1/triage/evaluate \
  -H "Content-Type: application/json" \
  -d '{"tenant_id":"11111111-1111-4111-8111-111111111111","facility_id":"22222222-2222-4222-8222-222222222222","encounter_id":"33333333-3333-4333-8333-333333333333","input_version":1,"idempotency_key":"setup-example-1","language":"en","chief_complaint":"My chest feels heavy","confirmed_answers":{}}'
```

PowerShell alternative:

```powershell
$triageBody = @{
  tenant_id = "11111111-1111-4111-8111-111111111111"
  facility_id = "22222222-2222-4222-8222-222222222222"
  encounter_id = "33333333-3333-4333-8333-333333333333"
  input_version = 1
  idempotency_key = "setup-example-1"
  language = "en"
  chief_complaint = "My chest feels heavy"
  confirmed_answers = @{}
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/v1/triage/evaluate -ContentType "application/json" -Body $triageBody
```

The response should use `phase6.prototype.v1`, return the stable rule ID
`RF-CARDIAC-001`, and state `"durable_alert_created":false`. A result of
`no_configured_flag` means only that no configured prototype rule matched; it
does not mean routine or safe.

### Stop the stack

```bash
docker compose down
```

This preserves database volumes. To remove local databases and object-storage data as well, run `docker compose down --volumes` only when you intentionally want to erase the local development data.

If migration startup reports a checksum mismatch, the named volume was created
from an older edited development migration. Do not alter the stored checksum or
edit an already released migration. Preserve any data you need, then either use
a fresh database or—only for disposable local data—run `docker compose down
--volumes` before starting again. That command erases all local Compose database
and object-storage volumes.

### Use the Phase 7 document review locally

Development authentication is available only when `ENABLE_DEMO_ROUTES=true`.
Create a synthetic doctor token (never use this route outside local development):

```bash
curl -X POST "http://localhost:8000/api/v1/auth/token?user_id=aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa&email=doctor%40example.test&role=doctor&tenant_id=11111111-1111-4111-8111-111111111111&facility_ids=22222222-2222-4222-8222-222222222222"
```

Copy the returned `token` value, open the clinician console browser developer
console, and run:

```javascript
sessionStorage.setItem("medikiosk.access_token", "PASTE_TOKEN_HERE");
location.assign("/documents/review");
```

The queue is empty until a document is registered and reaches
`review_required`. Use the API documentation at <http://localhost:8000/docs>
to exercise the authorized upload-init/finalize endpoints with synthetic PNG,
JPEG, WebP or bounded PDF data. The pipeline runs quarantine → ClamAV scan →
page normalization → OCR → prescription extraction. In the review screen,
inspect the short-lived source preview, then accept, correct or reject each
candidate before finalizing. Accepted/corrected facts are promoted with
`document_stated` semantics; review does not assert that a medication is current.

If OCR or extraction is disabled or fails after pages were normalized, an
authorized nurse/doctor can open manual review through
`POST /api/v1/document-reviews/{document_id}/manual`, add source-linked manual
candidates, and finalize normally. See the
[document-pipeline runbook](infrastructure/runbooks/PHASE-7-DOCUMENT-PIPELINE.md).

### Use the Phase 8 summary workflow locally

Enable `ENABLE_DEMO_ROUTES=true` and `SUMMARY_WORKFLOW_ENABLED=true`. Open
<http://localhost:3001/login>, choose **Doctor**, and enter synthetic UUIDs for
the user, tenant and permitted facility. **Start local clinical session** obtains
the demo token from the local API and opens `/doctor`; no browser-console setup
is required. This login is deliberately demo-gated and is not production SSO.

In <http://localhost:8000/docs>, authorize with `Bearer PASTE_TOKEN_HERE` and:

1. `PUT /api/v1/summary-workflows/contexts` to confirm a synthetic encounter's
   facility, patient, chief complaint and answers. Use UUIDs and a facility ID
   included in the token.
2. `POST /api/v1/summary-workflows/generate` with the same facility, patient and
   encounter IDs and an `Idempotency-Key`. Do not send clinical narrative to
   this endpoint; the server loads the confirmed context.
3. Open <http://localhost:3001/doctor>, paste the encounter UUID and choose
   **Load summary**.
4. Edit and **Save draft**, or provide a reason and **Reject**. A rejected/draft
   version can be **Regenerated** as a separate generation.
5. Choose **Submit review**, then **Sign & lock** as a doctor. Signed content is
   immutable. This engineering signature is an integrity hash, not a legal
   digital-signature claim.

Nurses may confirm, generate, read and submit, but cannot edit, reject,
regenerate or sign. Warning flags are read-only. Use synthetic data only; this
workflow has engineering tests but no clinical/production approval.

### Use the patient workflow locally

Enable the complete demo flags from section 3, then open
<http://localhost:3000>. The production patient runtime is
`apps/patient-kiosk`; `frontend/apps/patient-dashboard` is a non-runtime scaffold.

1. Choose **Start case taking**. The app creates an opaque kiosk session and a
   synthetic patient development session; no record data is available to the
   kiosk pre-auth token.
2. Review and grant bounded treatment consent. The consent is stored in
   PostgreSQL and can later be revoked from <http://localhost:3000/consents>.
3. Choose **Assisted questions**. Confirm or correct each captured answer before
   it feeds the next mock-provider SOCRATES question. The mock TTS control plays
   an acknowledgement tone, not intelligible clinical speech.
4. Accept or reject the editable summary draft. That decision is durably stored
   as patient-confirmed intake; it is not a signed record.
5. Open <http://localhost:3000/records/upload> to upload a synthetic PNG, JPEG,
   WebP or bounded PDF. The patient ID is taken from the token, the object goes
   directly to quarantine, and the UI reports the real scan/OCR/review state.
6. Open <http://localhost:3000/records> to see only clinician-signed reports and
   clinician-reviewed document facts. Drafts and raw OCR are deliberately absent.

All patient record APIs are under `/api/v1/patient-portal/me`. They derive the
patient, tenant and permitted facilities from the token. See
[`docs/contracts/PATIENT-PORTAL-API.md`](docs/contracts/PATIENT-PORTAL-API.md).

## 5. Frontend-only development

Run each application in a separate terminal. The API URL defaults to
`http://localhost:8000`. The doctor page and patient records, consent and upload
pages require the API and a stored development token. Nurse-only demonstration
cards still contain clearly labelled synthetic content.

### Patient experience — port 3000

```bash
cd apps/patient-kiosk
npm ci
npm run dev -- --port 3000
```

### Nurse and doctor experience — port 3001

```bash
cd apps/clinician-console
npm ci
npm run dev -- --port 3001
```

### Admin console — port 3002

```bash
cd apps/admin-console
npm ci
npm run dev -- --port 3002
```

When running a frontend against a different API, copy its `.env.example` to `.env.local` and update `NEXT_PUBLIC_API_URL` before starting the development server.

## 6. Backend development outside Docker

Start only the infrastructure services:

```bash
docker compose up -d postgres mongodb redis kafka minio minio-init clamav
```

Create and activate a virtual environment.

Windows PowerShell:

```powershell
cd apps/api
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
Copy-Item .env.example .env
python -m app.migrations up
uvicorn app.main:app --reload --port 8000
```

macOS/Linux:

```bash
cd apps/api
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
cp .env.example .env
python -m app.migrations up
uvicorn app.main:app --reload --port 8000
```

Dialogue and TTS remain mocks. The dedicated Compose OCR worker includes the
real PP-OCRv5 mobile CPU runtime and downloads its public model artifacts into named
cache volumes on first start. When running that worker directly, install
`.[dev,ai-ocr-fast]`; a Hugging Face credential is not required because the
documented local configuration uses Paddle's public BOS model source.

## 7. How to use the prototype

### Patient

1. Open <http://localhost:3000>.
2. Switch between Hindi and English.
3. Start a case, review the treatment consent and choose voice-assisted or manual entry.
4. In **Assisted questions**, record or type an answer, confirm/correct it, and
   continue through adaptive SOCRATES questions from the offline mock provider.
5. Edit and accept/reject the summary draft; the API stores the real decision.
6. Use **My records** to view/download signed reports, review the reviewed-fact
   timeline, manage consent and upload a synthetic document into the OCR pipeline.
7. Use the accessibility controls to test larger text, higher contrast and
   assistant/emergency status announcements.

Browser microphone permission is needed only when exercising real recording components. Do not record real patient conversations in local development.

### Nurse

1. Open <http://localhost:3001>.
2. Review the deterministic urgency summary and live triage queue.
3. Filter the queue to urgent patients.
4. Review vitals, rule-owned alerts and handoff status.
5. Choose **Open handoff** to move into the doctor review workflow.

### Doctor

1. Open <http://localhost:3001/doctor>.
2. Paste a synthetic encounter UUID whose context and draft were created through the API.
3. Compare each editable section with its evidence paths and visible uncertainties.
4. Save the draft, reject/regenerate when necessary, or submit it for review.
5. Sign an in-review draft. The durable version is locked after signing.

## 8. Development checks

Run these inside each frontend application:

```bash
npm run lint
npm run build
```

Run API tests:

```bash
cd apps/api
pytest
ruff check app tests
mypy app
```

Run the live Phase 7 integration suite while the Compose infrastructure is up.

Windows PowerShell:

```powershell
$env:PHASE7_INTEGRATION = "1"
pytest tests/test_phase7_document_integration.py tests/test_phase7_ocr_integration.py -q
Remove-Item Env:PHASE7_INTEGRATION
```

macOS/Linux:

```bash
PHASE7_INTEGRATION=1 pytest tests/test_phase7_document_integration.py tests/test_phase7_ocr_integration.py -q
```

Run the Phase 8 unit/API tests and live PostgreSQL suite:

Windows PowerShell:

```powershell
pytest tests/test_phase8_summary_service.py tests/test_phase8_summary_api.py tests/test_phase8_outbox_publisher.py -q
$env:PHASE8_INTEGRATION = "1"
pytest tests/test_phase8_summary_integration.py -q
Remove-Item Env:PHASE8_INTEGRATION
```

macOS/Linux:

```bash
pytest tests/test_phase8_summary_service.py tests/test_phase8_summary_api.py tests/test_phase8_outbox_publisher.py -q
PHASE8_INTEGRATION=1 pytest tests/test_phase8_summary_integration.py -q
```

Run the self-scoped patient portal integration suite against the same local
PostgreSQL service. It creates and removes an isolated schema and does not touch
the application's `public` schema.

Windows PowerShell:

```powershell
$env:PATIENT_PORTAL_INTEGRATION = "1"
pytest tests/test_patient_portal_integration.py -q
Remove-Item Env:PATIENT_PORTAL_INTEGRATION
```

macOS/Linux:

```bash
PATIENT_PORTAL_INTEGRATION=1 pytest tests/test_patient_portal_integration.py -q
```

Run the frozen synthetic prescription-extraction evaluation:

```bash
python tools/evaluate_phase7_extraction.py ../../tests/model-evaluations/phase7/manifest.jsonl
```

Its perfect candidate score covers seven synthetic OCR-region fixtures only.
It does not measure real OCR, handwriting, camera quality or clinical safety,
and release thresholds still require owner approval.

Inspect container logs:

```bash
docker compose logs -f api
docker compose logs -f patient-kiosk clinician-console
```

## 9. Troubleshooting

### A port is already in use

Stop the conflicting process or change the host-side port in `docker-compose.yml`. Keep `CORS_ALLOWED_ORIGINS` aligned with any new frontend origins.

### Docker reports an unhealthy dependency

```bash
docker compose ps
docker compose logs postgres mongodb redis kafka
```

Restart the affected service after reviewing its log:

```bash
docker compose restart <service-name>
```

### A frontend cannot reach the API

- Confirm <http://localhost:8000/healthz> responds.
- Confirm `NEXT_PUBLIC_API_URL=http://localhost:8000`.
- Restart the Next.js process after changing an environment file.
- Confirm the frontend origin is present in `CORS_ALLOWED_ORIGINS`.

### Shared design-system CSS cannot be resolved

Run commands from the repository paths shown above. The patient and clinician apps intentionally resolve `packages/ui-system` through the repository-level Next.js build root.

### OneDrive or antivirus makes builds slow on Windows

Clone the repository into a short local path outside a synchronized folder, such as `C:\dev\NotMID`, and exclude project `node_modules` and `.next` directories from real-time indexing where organizational policy permits.

### Reset only generated frontend output

Stop the development server, remove the affected app's `.next` directory, and run the build again. Do not remove database volumes unless a full local-data reset is intended.

## 10. Current limitations

- Patient consent, confirmed intake, document state and signed-report views use
  durable APIs. Local identity remains a synthetic demo boundary; do not use it
  with real patient information.
- Phase 8 sign-off is durable, version-locked and hash-bound, but the engineering
  integrity hash is not represented as a legally qualified digital signature.
- Clerk and hospital SSO integration are not required for the local prototype and are not production-configured.
- Demo API routes are disabled by default. Set `ENABLE_DEMO_ROUTES=true` in `.env` only for local contract/UI prototyping; those routes do not provide production authorization or persistence guarantees.
- Phase 5 intentionally has no vLLM integration. Any generative provider requires separate clinical, privacy, licensing and rollback approval.
- Mock TTS emits a deterministic acknowledgement WAV, not intelligible speech.
  Production bilingual TTS needs separate accessibility, privacy and quality approval.
- Phase 6 Slice 6.1 provides a canonical prototype evaluator only. Durable flags,
  staff ownership, acknowledgement, escalation, outbox delivery, clinical
  approval and measured validation are not implemented.
- Phase 7 is an engineering candidate for prescription documents. Durable
  registry/quarantine, scan/normalization/OCR/extraction workers, source-adjacent
  review, reviewed-fact promotion and an outbox publisher are implemented and
  integration-tested locally. Real OCR/camera/handwriting evaluation,
  accessibility sessions, operational drills and owner approvals remain open.
- Lab-table extraction is deliberately deferred until a governed table/unit/
  locale evaluation set and thresholds are approved.
- Production deployment requires managed secrets, TLS, authenticated data services, backups, monitoring and reviewed clinical-safety controls.

For product behavior see [`PRODUCT.md`](PRODUCT.md). For the visual system see [`DESIGN.md`](DESIGN.md). For architecture and safety constraints start with [`CONTEXT-GRAPH.md`](CONTEXT-GRAPH.md) and [`AGENTS.md`](AGENTS.md).
