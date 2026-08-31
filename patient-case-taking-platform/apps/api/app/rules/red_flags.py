"""Example clinician-approved red flag rules.
These are deterministic — no LLM involved."""
from app.rules.engine import RuleResult, Severity, engine


@engine.register
def chest_pain_red_flag(answers: dict, context: dict) -> RuleResult:
    complaint = answers.get("chief_complaint", "").lower()
    symptoms = [s.lower() for s in answers.get("symptoms", [])]

    if "chest pain" in complaint or "chest pain" in symptoms:
        radiation = any(s in symptoms for s in ["arm pain", "jaw pain", "back pain", "left arm"])
        if radiation:
            return RuleResult(
                rule_id="RF-001",
                rule_name="Chest Pain with Radiation",
                triggered=True,
                severity=Severity.CRITICAL,
                message="Chest pain with radiation — immediate clinical review required",
                requires_acknowledgement=True,
            )
    return RuleResult(
        rule_id="RF-001",
        rule_name="Chest Pain with Radiation",
        triggered=False,
        severity=Severity.CRITICAL,
        message="",
    )


@engine.register
def difficulty_breathing_red_flag(answers: dict, context: dict) -> RuleResult:
    complaint = answers.get("chief_complaint", "").lower()
    symptoms = [s.lower() for s in answers.get("symptoms", [])]

    if any(s in complaint for s in ["breathing", "breathless", "shortness of breath", "dyspnea"]) or \
       any(s in symptoms for s in ["breathing difficulty", "shortness of breath"]):
        return RuleResult(
            rule_id="RF-002",
            rule_name="Difficulty Breathing",
            triggered=True,
            severity=Severity.HIGH,
            message="Difficulty breathing reported — prioritize clinical review",
            requires_acknowledgement=True,
        )
    return RuleResult(
        rule_id="RF-002",
        rule_name="Difficulty Breathing",
        triggered=False,
        severity=Severity.HIGH,
        message="",
    )


@engine.register
def fever_with_rash_red_flag(answers: dict, context: dict) -> RuleResult:
    symptoms = [s.lower() for s in answers.get("symptoms", [])]
    fever = "fever" in symptoms or "fever" in answers.get("chief_complaint", "").lower()
    rash = "rash" in symptoms

    if fever and rash:
        return RuleResult(
            rule_id="RF-003",
            rule_name="Fever with Rash",
            triggered=True,
            severity=Severity.MEDIUM,
            message="Fever with rash — clinical evaluation recommended",
            requires_acknowledgement=False,
        )
    return RuleResult(
        rule_id="RF-003",
        rule_name="Fever with Rash",
        triggered=False,
        severity=Severity.MEDIUM,
        message="",
    )
