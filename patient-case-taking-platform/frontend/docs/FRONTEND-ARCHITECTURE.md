# Frontend Architecture

## Deployment boundary

Maintain three separate applications rather than a single role-switched dashboard. This provides clearer ownership, smaller permission surfaces, independent release cadence and simpler role-specific UX.

All three applications may use the same identity provider, but each receives its own audience/client configuration and allowed callback URLs.

## Application layers

| Layer | Responsibility |
|---|---|
| `src/app` | route composition, layouts, providers and error boundaries |
| `src/features` | user-visible business capabilities and feature state |
| `src/components` | app-specific composite presentation components |
| `src/lib` | app-owned adapters and utilities without business UI |
| `src/styles` | app theme entry point and global styling |
| `tests` | application integration and route tests |

## State rules

- Server data is fetched through the typed API client and remains the backend's authority.
- URL state represents shareable navigation/filter state where privacy permits.
- Short-lived form/session state stays in memory.
- Offline patient drafts use an encrypted, explicit queue with expiry and user-visible deletion.
- Do not copy server data into a general global store without a measured need.

## Authentication and authorization

- Use secure server-managed or HTTP-only cookie sessions where the deployment framework supports them.
- Route middleware provides early redirects, not final authorization.
- Every backend request is authorized independently.
- Step-up authentication is required for sensitive administration, exports and break-glass access.
- Session expiry must preserve safe unsaved work without leaking data to another shared-device user.

## Error and loading behavior

- Each route group has loading, empty, error and permission-denied states.
- Doctor signing clearly distinguishes saved draft, pending sync and signed state.
- AI/provider failure degrades to manual entry.
- Patient offline behavior never implies that unsynchronized clinical data reached the hospital.

## Security

- Apply strict CSP, frame protection, secure cookies and dependency integrity controls.
- Sanitize uploaded/rich document previews and never trust OCR/LLM markup.
- Redact clinical request/response bodies from monitoring.
- Clear sensitive memory/session state on logout, role change and kiosk reset.

