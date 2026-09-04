# Document Processing Worker

Consumes quarantined object references, performs scanning/OCR/extraction and produces reviewable results with page-level provenance. It never replaces the immutable source file.

This worker is an architectural boundary, not a deployed implementation. The
current repository contains the tested registry lifecycle, tenant-isolated
PostgreSQL migration/repository, quarantine upload adapter and demo-gated
synchronous OCR providers. Live PostgreSQL/MinIO integration, scanning, async
jobs, extraction and review remain in progress in
[`PHASE-7-DOCUMENT-INGESTION-OCR.md`](../../docs/plans/PHASE-7-DOCUMENT-INGESTION-OCR.md).
