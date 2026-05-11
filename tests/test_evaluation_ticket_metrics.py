from ood.evaluation import EvaluationCase, ExpectedCommandRisk, ExpectedIdentifier
from ood.evaluation_ticket_metrics import (
    evaluate_ticket_intelligence_case,
    summarize_ticket_intelligence_metrics,
)
from ood.models import CommandRisk, RoutingDecision, TicketAnalysis, TicketIdentifier


def _case(
    *,
    expected_intent: str = "Problem",
    expected_route: str = "selbst lösen",
    expected_identifiers: tuple[ExpectedIdentifier, ...] = (),
    expected_command_risks: tuple[ExpectedCommandRisk, ...] = (),
    expected_uncertainties: tuple[str, ...] = (),
) -> EvaluationCase:
    return EvaluationCase(
        id="case-1",
        query="query",
        expected_sources=("source.md",),
        forbidden_sources=(),
        expected_intent=expected_intent,
        expected_route=expected_route,
        expected_identifiers=expected_identifiers,
        expected_command_risks=expected_command_risks,
        expected_uncertainties=expected_uncertainties,
    )


def _analysis(
    *,
    intent: str = "Problem",
    route: str = "selbst lösen",
    identifiers: list[TicketIdentifier] | None = None,
    command_risks: list[CommandRisk] | None = None,
    uncertainties: list[str] | None = None,
) -> TicketAnalysis:
    return TicketAnalysis(
        intent=intent,
        assessment=None,
        solution_steps=[],
        routing=RoutingDecision(route=route, rationale="test"),
        identifiers=identifiers or [],
        command_risks=command_risks or [],
        uncertainties=uncertainties or [],
        mode="deterministic",
    )


def test_evaluate_ticket_intelligence_case_compares_intent_route_and_labels() -> None:
    metrics = evaluate_ticket_intelligence_case(
        _case(
            expected_identifiers=(ExpectedIdentifier(kind="police", value="mock-pol-1001"),),
            expected_command_risks=(ExpectedCommandRisk(command_contains="restart", risk="orange"),),
            expected_uncertainties=("fehlende Uhrzeit",),
        ),
        _analysis(
            identifiers=[TicketIdentifier(kind="police", value="MOCK-POL-1001", confidence=0.9, evidence="test")],
            command_risks=[CommandRisk(command="service restart worker", risk="orange", rationale="test", origin="source.md")],
            uncertainties=["Bitte fehlende Uhrzeit nachfragen."],
        ),
    )

    assert metrics.intent_match is True
    assert metrics.routing_match is True
    assert metrics.identifier_recall == 1.0
    assert metrics.command_risk_accuracy == 1.0
    assert metrics.uncertainty_match is True
    assert metrics.missing_identifiers == ()
    assert metrics.missing_command_risks == ()
    assert metrics.missing_uncertainties == ()


def test_evaluate_ticket_intelligence_case_reports_missing_expectations() -> None:
    metrics = evaluate_ticket_intelligence_case(
        _case(
            expected_intent="Request",
            expected_route="Rückfrage",
            expected_identifiers=(ExpectedIdentifier(kind="offerte", value="MOCK-OFF-2001"),),
            expected_command_risks=(ExpectedCommandRisk(command_contains="status", risk="grün"),),
            expected_uncertainties=("Mandant",),
        ),
        _analysis(intent="Problem", route="selbst lösen"),
    )

    assert metrics.intent_match is False
    assert metrics.routing_match is False
    assert metrics.identifier_recall == 0.0
    assert metrics.command_risk_accuracy == 0.0
    assert metrics.uncertainty_match is False
    assert metrics.missing_identifiers == (("offerte", "MOCK-OFF-2001"),)
    assert metrics.missing_command_risks == (("status", "grün"),)
    assert metrics.missing_uncertainties == ("Mandant",)


def test_evaluate_ticket_intelligence_case_scores_empty_expectations_as_perfect() -> None:
    metrics = evaluate_ticket_intelligence_case(_case(), _analysis())

    assert metrics.identifier_recall == 1.0
    assert metrics.command_risk_accuracy == 1.0
    assert metrics.uncertainty_match is True
    assert metrics.to_dict()["identifier_recall"] == 1.0


def test_summarize_ticket_intelligence_metrics_averages_dimensions() -> None:
    metrics = [
        evaluate_ticket_intelligence_case(_case(), _analysis()),
        evaluate_ticket_intelligence_case(
            _case(
                expected_intent="Request",
                expected_route="Rückfrage",
                expected_identifiers=(
                    ExpectedIdentifier(kind="police", value="MOCK-POL-1001"),
                    ExpectedIdentifier(kind="offerte", value="MOCK-OFF-2001"),
                ),
                expected_command_risks=(ExpectedCommandRisk(command_contains="restart", risk="orange"),),
                expected_uncertainties=("Mandant",),
            ),
            _analysis(
                intent="Request",
                route="selbst lösen",
                identifiers=[TicketIdentifier(kind="police", value="mock-pol-1001", confidence=0.8, evidence="test")],
                command_risks=[],
                uncertainties=[],
            ),
        ),
    ]

    summary = summarize_ticket_intelligence_metrics(metrics)

    assert summary.case_count == 2
    assert summary.intent_accuracy == 1.0
    assert summary.routing_accuracy == 0.5
    assert summary.identifier_recall == 0.75
    assert summary.command_risk_accuracy == 0.5
    assert summary.uncertainty_accuracy == 0.5
    assert summary.to_dict() == {
        "case_count": 2,
        "intent_accuracy": 1.0,
        "routing_accuracy": 0.5,
        "identifier_recall": 0.75,
        "command_risk_accuracy": 0.5,
        "uncertainty_accuracy": 0.5,
    }


def test_summarize_ticket_intelligence_metrics_handles_empty_lists() -> None:
    summary = summarize_ticket_intelligence_metrics([])

    assert summary.case_count == 0
    assert summary.intent_accuracy == 0.0
    assert summary.routing_accuracy == 0.0
    assert summary.identifier_recall == 0.0
    assert summary.command_risk_accuracy == 0.0
    assert summary.uncertainty_accuracy == 0.0
