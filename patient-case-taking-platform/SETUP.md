# MediKiosk Setup and Usage Guide

This guide is for developers, designers and reviewers starting MediKiosk on a new device. The recommended path uses Docker Compose and works on Windows, macOS and Linux.

> **Prototype notice:** the current dashboards use synthetic demonstration content. Do not enter real patient information. AI-assisted text is a draft and is not a diagnosis, prescription or signed medical record.

## 1. What starts locally

| Service | Address | Purpose |
|---|---|---|
| Patient experience | <http://localhost:3000> | Bilingual voice/touch-first intake |
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
LLM_PROVIDER=mock
OCR_PROVIDER=mock
DOCUMENT_OCR_AUTOMATION_ENABLED=true
DOCUMENT_EXTRACTION_AUTOMATION_ENABLED=true
```

`mock` is the only supported Phase 5 provider. The local stack does **not** start vLLM, download HiMed weights, require a GPU, or send patient text to an external model API.
The Phase 7 mock OCR provider is deterministic contract scaffolding; it is not
clinical OCR validation.

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

The Compose topology intentionally has no vLLM service. Phase 5 uses the mock
provider, and Phase 7 OCR uses the configured provider adapter.

To verify the mock clinical assistant after enabling demo routes:

```bash
curl http://localhost:8000/api/v1/clinical-ai/health
```

The response should report `"provider":"mock"`, `"ready":true` and `"external_network_used":false`. Then open <http://localhost:3000/case-taking/assisted>.

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

## 5. Frontend-only development

Run each application in a separate terminal. The API URL defaults to `http://localhost:8000`, but the redesigned dashboard screens render with synthetic data when the API is absent.

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

The default providers are mocks. Large ASR/OCR model dependencies and Hugging Face credentials are optional and are not required for dashboard development.

## 7. How to use the prototype

### Patient

1. Open <http://localhost:3000>.
2. Switch between Hindi and English.
3. Press the microphone control to see the listening state, or choose the touch flow.
4. Choose **Assisted Questions** to exercise adaptive SOCRATES questions through the offline mock provider, or continue through the fixed touch questionnaire.
5. Use the accessibility controls to test larger text and higher contrast.

Browser microphone permission is needed only when exercising real recording components. Do not record real patient conversations in local development.

### Nurse

1. Open <http://localhost:3001>.
2. Review the deterministic urgency summary and live triage queue.
3. Filter the queue to urgent patients.
4. Review vitals, rule-owned alerts and handoff status.
5. Choose **Open handoff** to move into the doctor review workflow.

### Doctor

1. Open <http://localhost:3001/doctor>.
2. Compare the editable draft with patient-confirmed evidence and attributed nurse notes.
3. Edit the assessment or plan.
4. Resolve the visibly marked missing information.
5. Use **Review & sign** to exercise the prototype sign-off state. This is a browser-only demonstration and does not create a durable medical record.

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

- The redesigned dashboards currently display synthetic demonstration data.
- The visual sign-off interaction is not yet a durable or authenticated clinical signature.
- Clerk and hospital SSO integration are not required for the local prototype and are not production-configured.
- Demo API routes are disabled by default. Set `ENABLE_DEMO_ROUTES=true` in `.env` only for local contract/UI prototyping; those routes do not provide production authorization or persistence guarantees.
- Phase 5 intentionally has no vLLM integration. Any generative provider requires separate clinical, privacy, licensing and rollback approval.
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
