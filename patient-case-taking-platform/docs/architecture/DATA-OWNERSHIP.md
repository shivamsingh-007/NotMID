# Data Ownership and Storage Plan

## Sources of truth

| Data | Owner | Primary store | Derived copies |
|---|---|---|---|
| Patient identity | Clinical platform / identity module | PostgreSQL | Search-safe lookup projection |
| Consent and delegation | Consent module | PostgreSQL + immutable audit | ABDM reconciliation view |
| Encounter answers | Encounter module | PostgreSQL | Summary/search projection |
| Signed clinical record | Clinical record module | PostgreSQL | FHIR document, search index |
| Raw audio and documents | Document registry | Object storage | Transcript, OCR and thumbnails |
| Document metadata | Document registry | PostgreSQL | OpenSearch projection |
| AI jobs and results | Owning workflow/worker | PostgreSQL | Operational metrics |
| Session/cache/limits | Owning service | Redis | None; safe to lose/recreate |
| Search | Search projector | OpenSearch | Rebuilt from authoritative data |
| Audit evidence | Audit component | Append-only/immutable store | Security analytics |

## Identity rules

- Generate a non-semantic internal patient UUID.
- Store ABHA number/address as verified external identifiers with status and timestamps.
- Permit care before ABHA creation or linking.
- Maintain merge and unmerge history; never destructively overwrite duplicate identities.
- Separate caregiver/delegate identity from the patient identity.

## Clinical provenance

Every normalized fact should link to its source:

`Clinical fact → encounter/document → source segment/page/utterance → extraction/model version → confirmation history`

## Retention and deletion

Retention periods must be approved by clinical, legal and facility governance. Implement legal hold, consent withdrawal effects, deletion/anonymization workflows and backup expiry as separate policies. Do not promise immediate physical deletion from immutable backups; document the actual lifecycle.

## Database choice

Begin with PostgreSQL plus JSONB for flexible FHIR representations. Do not introduce MongoDB until measured access patterns demonstrate a need not met by PostgreSQL. Use one managed OpenSearch product rather than operating both Elasticsearch and OpenSearch.

