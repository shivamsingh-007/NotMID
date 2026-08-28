# Security and Privacy Plan

## Identity and authorization

- Use Clerk as the authentication provider for staff and patient web surfaces; integrate hospital SSO where available.
- Treat Clerk as an identity proof/session issuer, not the authorization source of truth.
- FastAPI validates token signature, issuer, audience, expiry and authorized-party/client claims using cached, pinned JWKS metadata with bounded refresh behavior.
- Map Clerk identities to internal patient, caregiver or workforce identities; never use a Clerk ID as the patient or clinical-record primary key.
- Verify facility and practitioner relationships; keep HPR/HFR as external verification inputs.
- Use short-lived sessions, MFA for privileged roles and device/session revocation.
- Combine role, facility, care relationship, consent, purpose and record sensitivity in authorization decisions.
- Record emergency break-glass reason and notify governance reviewers.
- Verify Clerk webhook signatures, enforce idempotency and treat webhook data as identity lifecycle input rather than immediate clinical authorization.
- Kiosk anonymous/pre-auth sessions are opaque, short-lived and limited to starting intake; record search and PHI display require verified identity or an attributed staff-assisted flow.

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
- Clerk tenant/account mis-linking, webhook spoofing, stale revocation and identity-provider outage.
- Notification content exposed on shared phones.
- Unauthorized caregiver access.
- Stolen kiosk or shared-device session.
- Event replay, duplicate delivery and stale authorization caches.
- Malicious or incorrect patient merges.
