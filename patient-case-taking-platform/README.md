# Patient Case-Taking Platform

Planning-first repository scaffold for a multilingual, consent-driven patient case-taking platform for Indian hospitals.

This repository structure deliberately separates:

- patient and clinician experiences;
- core clinical transactions;
- asynchronous document and AI processing;
- ABDM/ABHA interoperability;
- clinical safety and model evaluation;
- deployable infrastructure and operational controls.

No production application code is included yet. The build should begin only after the Phase 0 decisions and exit gate in [`docs/plans/BUILD-ROADMAP.md`](docs/plans/BUILD-ROADMAP.md) are approved.

## Start here

1. [`CONTEXT-GRAPH.md`](CONTEXT-GRAPH.md) — repository and system context.
2. [`docs/plans/BUILD-ROADMAP.md`](docs/plans/BUILD-ROADMAP.md) — phased delivery plan.
3. [`docs/architecture/SYSTEM-ARCHITECTURE.md`](docs/architecture/SYSTEM-ARCHITECTURE.md) — target architecture and request flows.
4. [`docs/architecture/DATA-OWNERSHIP.md`](docs/architecture/DATA-OWNERSHIP.md) — sources of truth and storage rules.
5. [`docs/contracts/EVENT-CATALOG.md`](docs/contracts/EVENT-CATALOG.md) — asynchronous event conventions.
6. [`docs/safety/CLINICAL-AI-SAFETY.md`](docs/safety/CLINICAL-AI-SAFETY.md) — clinical AI safety gates.
7. [`docs/security/SECURITY-AND-PRIVACY.md`](docs/security/SECURITY-AND-PRIVACY.md) — consent, access and PHI controls.
8. [`frontend/README.md`](frontend/README.md) — separate patient, doctor and user-administration frontend structure.

## Proposed repository tree

```text
patient-case-taking-platform/
├── README.md
├── AGENTS.md
├── CONTEXT-GRAPH.md
├── apps/
│   ├── patient-pwa/             # Voice-first patient and caregiver experience
│   ├── clinician-web/           # Clinician review and signed clinical notes
│   ├── assisted-kiosk/          # Registration-desk and low-literacy workflow
│   └── operations-console/      # Support, audit and operational administration
├── services/
│   ├── clinical-platform/       # Modular core: identity, consent, encounters, records
│   ├── conversation-orchestrator/
│   ├── ai-model-gateway/
│   ├── document-processing-worker/
│   ├── summary-worker/
│   ├── alert-worker/
│   ├── notification-worker/
│   └── abdm-adapter/
├── packages/
│   ├── api-contracts/           # OpenAPI schemas and generated clients
│   ├── event-contracts/         # Kafka envelopes and event schemas
│   ├── fhir-profiles/           # FHIR R4/ABDM mappings and validation
│   ├── authorization/           # Shared RBAC/ABAC policy definitions
│   ├── observability/           # Logging, metrics and tracing conventions
│   ├── clinical-terminology/    # Versioned codes and mappings
│   └── ui-system/               # Accessible multilingual components
├── model-assets/
│   ├── prompts/                 # Versioned prompts without secrets or PHI
│   ├── evaluation-datasets/     # Synthetic/de-identified test fixtures only
│   ├── model-cards/
│   └── safety-policies/
├── infrastructure/
│   ├── environments/{local,dev,staging,production}/
│   ├── modules/{network,edge,compute,data,messaging,observability,secrets}/
│   ├── kubernetes/{base,overlays}/
│   └── runbooks/
├── docs/
│   ├── product/
│   ├── architecture/
│   ├── plans/
│   ├── contracts/
│   ├── ai/
│   ├── safety/
│   ├── security/
│   ├── ux/
│   ├── integrations/
│   └── operations/
├── tests/
│   ├── contract/
│   ├── end-to-end/
│   ├── clinical-safety/
│   ├── model-evaluations/
│   ├── security/
│   ├── accessibility/
│   └── performance/
└── tools/
    ├── local-development/
    ├── fixtures/
    └── migration/
```

## Architecture principles

1. Patient safety is a release gate, not a backlog item.
2. The clinician remains accountable for signed clinical content.
3. ABHA is an external identifier and consent pathway, not the internal primary key.
4. PostgreSQL is the transactional source of truth.
5. Object storage holds immutable source documents and audio.
6. OpenSearch, embeddings and summaries are derived and rebuildable.
7. Kafka carries events and object references, never large document bodies.
8. AI providers are reachable only through the model gateway.
9. Start with a modular clinical core; extract services only for scaling or isolation.
10. Every important clinical assertion retains provenance.
