# Clinical AI Safety Plan

## Intended use

AI may transcribe, translate, extract, organize, summarize and suggest follow-up questions. It must not independently diagnose, prescribe, sign records or suppress urgent escalation.

The current clinical dialogue and summary provider is the offline deterministic
mock only. No generative model weights or hosted model APIs are part of the
runtime. Mock output is still untrusted draft content and receives the same
schema, evidence and clinician-review controls.

## Safety layers

1. Deterministic interview state and required-field rules.
2. Explicit patient confirmation of interpreted answers.
3. Deterministic urgent-symptom screening designed with clinicians.
4. Model confidence and uncertainty handling.
5. Source-linked draft summary.
6. Clinician correction and sign-off.
7. Post-release monitoring and incident review.

## Phase 8 summary controls

- A nurse or doctor confirms encounter context before generation; the generation
  endpoint accepts identifiers rather than client-authored clinical context.
- The server recomputes Phase 6 rules and adds only active, reviewed Phase 7 facts.
- Deterministic warning flags cannot be removed by mock output or doctor editing.
- Malformed provider output retries at most three times, then uses a marked
  deterministic template for manual review.
- Nurses may generate/read/submit; only doctors may edit, reject, regenerate or sign.
- Every mutation uses optimistic concurrency and append-only metadata history.
- Signing requires `in_review`, stores a canonical SHA-256 integrity hash and
  locks the version. The hash is not represented as a legal digital signature.
- Regeneration creates a linked version and never rewrites signed history.
- Audit and outbox metadata exclude chief complaint, answers and narrative content.

## Release gates

Measure separately by language, code-switching pattern, microphone quality, sex/age cohorts where permitted, and clinical category:

- critical symptom recall;
- clinically meaningful omission rate;
- unsupported assertion/hallucination rate;
- medication and allergy extraction accuracy;
- negation and temporality accuracy;
- ASR medical-term error rate;
- clinician material-edit rate;
- patient correction and comprehension rates.

Thresholds must be approved by the clinical-safety owner before pilot use.

## Model change control

Every model, provider, prompt or decoding change requires:

- versioned configuration and model card;
- offline evaluation against frozen and newly sampled cases;
- privacy and security review;
- shadow or canary rollout;
- rollback trigger and procedure;
- comparison against the currently approved baseline.

## Failure behavior

- Model unavailable: switch to manual structured entry.
- Low calibrated ASR confidence, empty text, or poor acoustic signal quality: ask for clarification and offer manual correction. Never present acoustic quality as model confidence.
- Conflicting records: show conflict; do not silently resolve it.
- Suspected emergency: stop routine questioning and present facility-approved escalation.
- Unsupported language: use assisted workflow; do not pretend successful understanding.
