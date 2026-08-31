"""Deterministic rules engine skeleton.
Rules are clinician-owned, testable, and versioned.
No LLM is the sole red-flag detector."""
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RuleResult:
    rule_id: str
    rule_name: str
    triggered: bool
    severity: Severity
    message: str
    requires_acknowledgement: bool = False


Rule = Callable[[dict, dict], RuleResult]


class RulesEngine:
    def __init__(self, version: str = "1.0.0"):
        self.version = version
        self._rules: list[Rule] = []

    def register(self, rule_func: Rule) -> Rule:
        self._rules.append(rule_func)
        return rule_func

    def evaluate(self, answers: dict, context: dict | None = None) -> list[RuleResult]:
        results: list[RuleResult] = []
        for rule in self._rules:
            result = rule(answers, context or {})
            if result.triggered:
                results.append(result)
        return results


engine = RulesEngine()
