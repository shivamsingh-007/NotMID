"""Prompt identifiers retained for compatibility with future evaluated providers.

The mock provider does not execute free-form prompts. Keeping versioned task
instructions here lets a future provider implement the same contract only after
its separate clinical, privacy, and model-quality approval.
"""

DIALOGUE_PROMPT_VERSION = "clinical-dialogue-v1"
SUMMARY_PROMPT_VERSION = "clinical-summary-v1"

CLINICAL_BOUNDARIES = (
    "Collect information without diagnosing or prescribing. "
    "Never suppress deterministic red-flag escalation. "
    "Clearly mark uncertainty and require clinician review."
)
