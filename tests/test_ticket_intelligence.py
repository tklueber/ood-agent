from ood.models import ConfidenceScore, SourceHit
from ood.ticket_intelligence import analyze_ticket


def test_intent_classification_uses_problem_question_and_request_signals() -> None:
    confidence = ConfidenceScore(score=0.8, rationale="test")
    sources = [SourceHit(path="runbook.md", score=0.9, excerpt="Use status command.")]

    assert analyze_ticket("Fehler: Login stürzt ab", sources, confidence).intent == "Problem"
    assert analyze_ticket("Wie behebe ich den Fehler?", sources, confidence).intent == "Frage"
    assert analyze_ticket("Bitte neuen Zugang einrichten", sources, confidence).intent == "Request"
    assert analyze_ticket("FYI", sources, confidence).intent == "Unklar"


def test_identifier_extraction_is_context_aware_for_policy_and_quote_numbers() -> None:
    analysis = analyze_ticket(
        "Police P-12345 und Offertennummer 456789 prüfen; Nummer 999 bleibt ignoriert.",
        [SourceHit(path="handoff.md", score=0.8, excerpt="Police team handles policies.")],
        ConfidenceScore(score=0.8, rationale="test"),
    )

    assert [(identifier.kind, identifier.value) for identifier in analysis.identifiers] == [
        ("police", "P-12345"),
        ("offerte", "456789"),
    ]


def test_routing_prefers_uncertainty_then_domain_handoff_then_self_service() -> None:
    source = SourceHit(path="runbook.md", score=0.9, excerpt="Restart the worker.")

    assert analyze_ticket("Fehler", [], ConfidenceScore(score=0.8, rationale="test")).routing.route == "Rückfrage"
    assert analyze_ticket("Fehler", [source], ConfidenceScore(score=0.2, rationale="test")).routing.route == "Rückfrage"
    assert analyze_ticket("Police P-12345 Fehler", [source], ConfidenceScore(score=0.8, rationale="test")).routing.route == "weiterleiten Policen"
    assert analyze_ticket("Offerte O-456 Frage", [source], ConfidenceScore(score=0.8, rationale="test")).routing.route == "weiterleiten Offerten"
    assert analyze_ticket("Worker Fehler", [source], ConfidenceScore(score=0.8, rationale="test")).routing.route == "selbst lösen"


def test_command_risk_detection_uses_ticket_and_source_origins() -> None:
    analysis = analyze_ticket(
        "Bitte rm -rf /tmp/cache ausführen und status prüfen",
        [SourceHit(path="runbook.md", score=0.9, excerpt="Run kubectl get pods, then restart service worker.")],
        ConfidenceScore(score=0.9, rationale="test"),
    )

    risks = {(risk.command, risk.risk, risk.origin) for risk in analysis.command_risks}
    assert ("rm -rf /tmp/cache", "rot", "ticket") in risks
    assert ("status", "grün", "ticket") in risks
    assert ("kubectl get pods", "grün", "runbook.md") in risks
    assert ("restart service worker", "orange", "runbook.md") in risks


def test_uncertainties_are_reported_for_no_sources_low_confidence_and_unclear_intent() -> None:
    analysis = analyze_ticket("FYI", [], ConfidenceScore(score=0.2, rationale="test"))

    assert analysis.mode == "deterministic"
    assert analysis.assessment is None
    assert analysis.solution_steps == []
    assert analysis.uncertainties == [
        "Keine belastbaren Quellen gefunden.",
        "Niedrige Retrieval-Confidence.",
        "Intent nicht eindeutig.",
    ]
