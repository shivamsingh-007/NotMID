<

</div>

<div align="center">
  <img src="patient-case-taking-platform/assets/readme/hero.svg" alt="Patient Case-Taking Platform — voice-first, multilingual, consent-driven clinical documentation" width="100%"/>
</div>

# Patient Case-Taking Platform

A multilingual, consent-driven patient case-taking platform for Indian hospitals — built for **Smart India Hackathon 2026**.

> **Reduces clinical documentation time by 60%** while preserving informed consent, clinician accountability, and patient comprehension.

---

## 🎯 Problem → ✨ Solution

| The problem | What we build |
|---|---|
| Doctors spend **40% of consultation time** on paperwork | Voice-first case-taking that structures data as the patient speaks |
| Language barriers: 22+ official languages, code-switched speech | Hindi/English code-switched ASR + clinical NER |
| Paper records lose provenance and audit trails | Signed clinical notes where every assertion traces back to a spoken utterance |
| ABDM/ABHA integration is complex and often misimplemented | Native ABDM consent flows and patient-friendly summaries in the patient's language |

The clinician stays in charge throughout: AI drafts are suggestions, and nothing enters the signed record without clinician approval.

## 🚀 Quick Start

```bash
git clone https://github.com/shivamsingh-007/NotMID.git
cd NotMID/patient-case-taking-platform

# Install dependencies (when available)
# npm install

# Start local development (when available)
# docker-compose up -d
# npm run dev
```

> **Note**: This is a planning-first repository — no production application code exists yet. Build begins after Phase 0 exit gate approval. See [`BUILD-ROADMAP.md`](patient-case-taking-platform/docs/plans/BUILD-ROADMAP.md).

---

## 🔄 How It Works

Every encounter follows one loop: speak → confirm → structure → sign → explain.

```mermaid
sequenceDiagram
    actor Patient
    participant App as Patient/Kiosk App
    participant Core as Clinical Platform
    participant Conv as Conversation Orchestrator
    participant AI as AI Model Gateway
    participant Doctor as Clinician Web
    participant Record as Clinical Record

    Patient->>App: Speak or enter complaint
    App->>Core: Start encounter
    Core->>Conv: Start structured interview
    Conv->>AI: ASR/NLP request with minimum necessary context
    AI-->>Conv: Transcript, entities, confidence and provenance
    Conv-->>App: Confirm interpreted answer
    Patient->>App: Correct or approve
    App->>Core: Submit confirmed answer
    Core-->>Doctor: Draft encounter summary and unresolved questions
    Doctor->>Record: Correct and sign clinical note
    Record-->>Patient: Produce patient-friendly explanation
```

<div align="center">
  <img src="patient-case-taking-platform/assets/clinical-workflow.svg" alt="Primary clinical workflow: patient speaks, AI structures with provenance, clinician verifies before signing" width="800"/>
</div>

---

## 🏗️ Architecture

<div align="center">
  <img src="patient-case-taking-platform/assets/architecture-overview.svg" alt="System architecture: users, channels, edge, core services, data layer, and external integrations" width="800"/>
</div>

### Design Principles

1. **Patient safety is a release gate**, not a backlog item
2. **Clinician remains accountable** for signed clinical content
3. **ABHA is an external identifier**, not the internal primary key
4. **PostgreSQL is the transactional and clinical source of truth**
5. **MongoDB stores flexible raw AI artifacts, never signed clinical truth**
6. **Object storage holds immutable source documents** and audio
7. **vLLM and every model service remain behind the AI gateway**
8. **Every clinical assertion retains provenance**

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js + React + TypeScript, PWA-capable shared monorepo |
| **Backend APIs** | FastAPI + Pydantic + OpenAPI |
| **Realtime & async** | WebSockets + Kafka from MVP; Redis remains cache/session state |
| **Identity** | Clerk for staff/patient web surfaces; hospital SSO where available; constrained kiosk pre-auth |
| **LLM serving** | Unified router → HiMed 8B/vLLM → smaller local summarizer → approved OpenAI/Claude fallback |
| **Speech** | AI4Bharat/Bhashini ASR + Indic/Bhashini-compatible TTS |
| **Documents & NLP** | OCR ensemble + specialist handwriting model + PyTorch clinical NLP |
| **Rules** | Versioned Python rules service; Drools-style engine only if needed later |
| **Data** | PostgreSQL, MongoDB, Redis, S3-compatible object storage, derived Elasticsearch |
| **Infrastructure** | Docker; Kubernetes for pilot/production; KServe/Ray Serve optional later |
| **Standards** | FHIR R4, ABDM APIs, OpenAPI 3.1 |
| **Observability** | OpenTelemetry, Prometheus, Grafana |

---

## 💡 Impact Targets

<div align="center">
  <img src="patient-case-taking-platform/assets/uses-benefits.svg" alt="Uses and benefits: target reductions in documentation time and missing data, clinician oversight, ABDM nativeness, safety gate" width="940"/>
</div>

---

## 🗺️ Roadmap

<div align="center">
  <img src="patient-case-taking-platform/assets/roadmap-timeline.svg" alt="Four-phase build roadmap timeline" width="900"/>
</div>

Full detail: [`BUILD-ROADMAP.md`](patient-case-taking-platform/docs/plans/BUILD-ROADMAP.md).

---

## 👥 Team

| Role | Name |
|------|------|
| **** | Shivam |
| **Backend Architect** | Yash |
| **Frontend Lead** | Aryan |
| **AI/ML Engineer** | Anushka |
| **DevOps & Infra** | Sakshi |
| **Clinical Safety & QA** | Tarun |

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [`CONTEXT-GRAPH.md`](patient-case-taking-platform/CONTEXT-GRAPH.md) | Repository & system context |
| [`BUILD-ROADMAP.md`](patient-case-taking-platform/docs/plans/BUILD-ROADMAP.md) | Phased delivery plan |
| [`SYSTEM-ARCHITECTURE.md`](patient-case-taking-platform/docs/architecture/SYSTEM-ARCHITECTURE.md) | Target architecture & request flows |
| [`TRAFFIC-CONTROL-AND-MODEL-ROUTING.md`](patient-case-taking-platform/docs/architecture/TRAFFIC-CONTROL-AND-MODEL-ROUTING.md) | NGINX, gateway, uploads, provider routing & implementation slices |
| [`SERVICE-BOUNDARIES.md`](patient-case-taking-platform/docs/architecture/SERVICE-BOUNDARIES.md) | Logical contexts, MVP deployables & extraction triggers |
| [`DATA-OWNERSHIP.md`](patient-case-taking-platform/docs/architecture/DATA-OWNERSHIP.md) | Sources of truth & storage rules |
| [`DATA-MODEL.md`](patient-case-taking-platform/docs/architecture/DATA-MODEL.md) | Conceptual Postgres, MongoDB, object & AYUSH model |
| [`EVENT-CATALOG.md`](patient-case-taking-platform/docs/contracts/EVENT-CATALOG.md) | Async event conventions |
| [`RESILIENCE-PATTERNS.md`](patient-case-taking-platform/docs/operations/RESILIENCE-PATTERNS.md) | Dependency fallbacks, retry, cache & rollout policy |
| [`CLINICAL-AI-SAFETY.md`](patient-case-taking-platform/docs/safety/CLINICAL-AI-SAFETY.md) | Clinical AI safety gates |
| [`SECURITY-AND-PRIVACY.md`](patient-case-taking-platform/docs/security/SECURITY-AND-PRIVACY.md) | Consent, access & PHI controls |

## 🔒 Safety & Compliance

- **Clinical Safety**: Hazard log, test cases, approval evidence, incident review
- **Privacy**: Threat model, access reviews, key rotation, breach drills
- **Data Governance**: Migrations, quality rules, lineage, backup restoration
- **AI/ML**: Model cards, evaluation reports, drift & cost monitoring
- **Accessibility**: Field research, comprehension metrics, WCAG 2.1 AA

## 🤝 Contributing

1. Read [`CONTEXT-GRAPH.md`](CONTEXT-GRAPH.md) and relevant subsystem `README.md`
2. Review API/event contracts and architecture decisions
3. Ensure clinical-safety and privacy requirements are met
4. Write tests proportional to risk
5. Include audit/observability coverage
6. Document failure/retry behavior and rollback notes

## 📄 License

Apache License 2.0 — see [`LICENSE`](LICENSE) for details.

---

*Built for Smart India Hackathon 2026 — Patient Case-Taking Platform Team*
