from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from ood.evaluation import EvaluationCase, ExpectedCommandRisk, ExpectedIdentifier
from ood.models import CommandRisk, TicketAnalysis, TicketIdentifier


@dataclass(frozen=True)
class TicketIntelligenceCaseMetrics:
    case_id: str
    intent_match: bool
    routing_match: bool
    identifier_recall: float
    command_risk_accuracy: float
    uncertainty_match: bool
    missing_identifiers: tuple[tuple[str, str], ...]
    missing_command_risks: tuple[tuple[str, str], ...]
    missing_uncertainties: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "intent_match": self.intent_match,
            "routing_match": self.routing_match,
            "identifier_recall": self.identifier_recall,
            "command_risk_accuracy": self.command_risk_accuracy,
            "uncertainty_match": self.uncertainty_match,
            "missing_identifiers": [list(identifier) for identifier in self.missing_identifiers],
            "missing_command_risks": [list(risk) for risk in self.missing_command_risks],
            "missing_uncertainties": list(self.missing_uncertainties),
        }


@dataclass(frozen=True)
class TicketIntelligenceMetricsSummary:
    case_count: int
    intent_accuracy: float
    routing_accuracy: float
    identifier_recall: float
    command_risk_accuracy: float
    uncertainty_accuracy: float

    def to_dict(self) -> dict[str, int | float]:
        return {
            "case_count": self.case_count,
            "intent_accuracy": self.intent_accuracy,
            "routing_accuracy": self.routing_accuracy,
            "identifier_recall": self.identifier_recall,
            "command_risk_accuracy": self.command_risk_accuracy,
            "uncertainty_accuracy": self.uncertainty_accuracy,
        }


def evaluate_ticket_intelligence_case(
    case: EvaluationCase, analysis: TicketAnalysis
) -> TicketIntelligenceCaseMetrics:
    """Compare expected ticket labels with public TicketAnalysis output."""

    missing_identifiers = _missing_identifiers(case.expected_identifiers, analysis.identifiers)
    missing_command_risks = _missing_command_risks(
        case.expected_command_risks, analysis.command_risks
    )
    missing_uncertainties = _missing_uncertainties(
        case.expected_uncertainties, analysis.uncertainties
    )

    return TicketIntelligenceCaseMetrics(
        case_id=case.id,
        intent_match=case.expected_intent == analysis.intent,
        routing_match=case.expected_route == analysis.routing.route,
        identifier_recall=_recall(case.expected_identifiers, missing_identifiers),
        command_risk_accuracy=_recall(case.expected_command_risks, missing_command_risks),
        uncertainty_match=not missing_uncertainties,
        missing_identifiers=missing_identifiers,
        missing_command_risks=missing_command_risks,
        missing_uncertainties=missing_uncertainties,
    )


def summarize_ticket_intelligence_metrics(
    metrics: list[TicketIntelligenceCaseMetrics],
) -> TicketIntelligenceMetricsSummary:
    """Aggregate ticket-intelligence metrics into report-ready rates."""

    case_count = len(metrics)
    if case_count == 0:
        return TicketIntelligenceMetricsSummary(
            case_count=0,
            intent_accuracy=0.0,
            routing_accuracy=0.0,
            identifier_recall=0.0,
            command_risk_accuracy=0.0,
            uncertainty_accuracy=0.0,
        )

    return TicketIntelligenceMetricsSummary(
        case_count=case_count,
        intent_accuracy=_rounded_mean(1.0 if metric.intent_match else 0.0 for metric in metrics),
        routing_accuracy=_rounded_mean(1.0 if metric.routing_match else 0.0 for metric in metrics),
        identifier_recall=_rounded_mean(metric.identifier_recall for metric in metrics),
        command_risk_accuracy=_rounded_mean(metric.command_risk_accuracy for metric in metrics),
        uncertainty_accuracy=_rounded_mean(1.0 if metric.uncertainty_match else 0.0 for metric in metrics),
    )


def _missing_identifiers(
    expected: tuple[ExpectedIdentifier, ...], actual: list[TicketIdentifier]
) -> tuple[tuple[str, str], ...]:
    actual_pairs = {(identifier.kind, identifier.value.casefold()) for identifier in actual}
    missing: list[tuple[str, str]] = []
    for identifier in expected:
        if (identifier.kind, identifier.value.casefold()) not in actual_pairs:
            missing.append((identifier.kind, identifier.value))
    return tuple(missing)


def _missing_command_risks(
    expected: tuple[ExpectedCommandRisk, ...], actual: list[CommandRisk]
) -> tuple[tuple[str, str], ...]:
    missing: list[tuple[str, str]] = []
    for expectation in expected:
        expected_command = expectation.command_contains.casefold()
        expected_risk = expectation.risk
        if not any(
            expected_command in risk.command.casefold() and risk.risk == expected_risk
            for risk in actual
        ):
            missing.append((expectation.command_contains, expectation.risk))
    return tuple(missing)


def _missing_uncertainties(
    expected: tuple[str, ...], actual: list[str]
) -> tuple[str, ...]:
    actual_text = "\n".join(actual).casefold()
    return tuple(expectation for expectation in expected if expectation.casefold() not in actual_text)


def _recall(expected: tuple[object, ...], missing: tuple[object, ...]) -> float:
    if not expected:
        return 1.0
    return round((len(expected) - len(missing)) / len(expected), 4)


def _rounded_mean(values: Iterable[float]) -> float:
    value_list = list(values)
    if not value_list:
        return 0.0
    return round(sum(value_list) / len(value_list), 4)


__all__ = [
    "TicketIntelligenceCaseMetrics",
    "TicketIntelligenceMetricsSummary",
    "evaluate_ticket_intelligence_case",
    "summarize_ticket_intelligence_metrics",
]
