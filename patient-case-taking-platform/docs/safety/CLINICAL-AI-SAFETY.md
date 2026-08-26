# Clinical AI Safety Plan

## Intended use

AI may transcribe, translate, extract, organize, summarize and suggest follow-up questions. It must not independently diagnose, prescribe, sign records or suppress urgent escalation.

## Safety layers

1. Deterministic interview state and required-field rules.
2. Explicit patient confirmation of interpreted answers.
3. Deterministic urgent-symptom screening designed with clinicians.
4. Model confidence and uncertainty handling.
5. Source-linked draft summary.
6. Clinician correction and sign-off.
7. Post-release monitoring and incident review.

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
- Low ASR confidence: replay and ask for confirmation or manual correction.
- Conflicting records: show conflict; do not silently resolve it.
- Suspected emergency: stop routine questioning and present facility-approved escalation.
- Unsupported language: use assisted workflow; do not pretend successful understanding.

