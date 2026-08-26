# Security and Privacy Plan

## Identity and authorization

- Use workforce IAM for doctors, nurses, operators and administrators.
- Verify facility and practitioner relationships; keep HPR/HFR as external verification inputs.
- Use short-lived sessions, MFA for privileged roles and device/session revocation.
- Combine role, facility, care relationship, consent, purpose and record sensitivity in authorization decisions.
- Record emergency break-glass reason and notify governance reviewers.

## Patient consent

Consent records contain purpose, data categories, recipient, time range, expiry, delegation and revocation. ABDM consent exchange is implemented through the adapter; internal authorization still enforces local policy.

## PHI protection

- Encrypt transport and storage using managed keys.
- Use separate keys/scopes for object storage, databases and backups.
- Redact PHI from logs, traces, metrics and support tools.
- Tokenize/minimize data sent to external model providers.
- Use signed, short-lived object access; never public buckets.
- Prevent CDN caching of authenticated clinical content.
- Scan uploads and quarantine before processing.

## Audit events

Capture successful and denied access, searches, exports, consent changes, patient merges, note signatures, break-glass access, model-generated content acceptance and administrative policy changes.

## Threat-model priorities

- Cross-patient record mix-up.
- Broken facility/tenant isolation.
- Prompt injection from uploaded documents.
- Provider-side retention or training on PHI.
- Notification content exposed on shared phones.
- Unauthorized caregiver access.
- Stolen kiosk or shared-device session.
- Event replay, duplicate delivery and stale authorization caches.
- Malicious or incorrect patient merges.

