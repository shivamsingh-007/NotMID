# OpenCode Change Review — Verified Record

Reviewed on 2026-08-29. This file records evidence, not roadmap optimism.

## Accepted and improved

- Kept the three separate Next.js shells for patient kiosk, clinician console, and administration.
- Upgraded all shells from the vulnerable Next.js 14 baseline to Next.js 16.3.3 Active LTS with React 19, reproducible lockfiles, ESLint CLI configuration, standalone output, and non-root containers.
- Fixed the kiosk server/client callback build failure and invalid nested link/button markup.
- Kept the FastAPI domain prototype, corrected its packaging backend, added real dependency readiness probes, and made readiness return HTTP 503 when dependencies are unavailable.
- Replaced wildcard credentialed CORS with explicit origins, methods, and headers.
- Made all synthetic clinical, identity, consent, audit, AYUSH, and FHIR routes opt-in through `ENABLE_DEMO_ROUTES`; they are off by default.
- Corrected Kafka internal/external listeners, local-only port binding, dependency health checks, and local-development credential labeling in Docker Compose.
- Corrected GitHub Actions working directories and aligned its commands with the repository layout.
- Removed the duplicate `docs/adr` set; the canonical ADRs remain under `docs/architecture/decisions`.

## Verification performed

| Gate | Result |
|---|---|
| Patient kiosk lint + production build | Passed |
| Clinician console lint + production build | Passed |
| Admin console lint + production build | Passed |
| Frontend dependency audit | 0 known vulnerabilities in each lockfile |
| FastAPI Ruff check | Passed |
| FastAPI mypy check | Passed across 60 source files |
| FastAPI tests | 42 passed |
| Docker Compose config parse | Passed |
| GitHub Actions YAML parse | Passed |

## Explicitly not complete

This is a reviewed foundation prototype, not a production clinical system. Clerk token verification, durable repositories, database migrations, multi-tenant authorization, transactional audit, Kafka workflows, object-storage policy, ABDM sandbox integration, end-to-end browser tests, accessibility validation, load/security testing, deployment, backup/restore, and clinical governance remain pending.

The detailed visual review is in [`review/medikiosk-change-ledger.html`](review/medikiosk-change-ledger.html).
