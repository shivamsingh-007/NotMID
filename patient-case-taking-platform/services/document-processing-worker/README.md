# Document Processing Worker

Consumes quarantined object references, performs scanning/OCR/extraction and produces reviewable results with page-level provenance. It never replaces the immutable source file.

This worker is an architectural boundary, not a deployed implementation. The
current repository contains demo-gated synchronous OCR provider adapters only;
durable document registration, quarantine, scanning, async jobs, extraction and
review remain proposed in
[`PHASE-7-DOCUMENT-INGESTION-OCR.md`](../../docs/plans/PHASE-7-DOCUMENT-INGESTION-OCR.md).
