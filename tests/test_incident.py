from __future__ import annotations

from ood.incident import IncidentRoutingDecision, route_operational_incident


def test_police_15_routes_to_pkv_without_solution_continuation() -> None:
    decision = route_operational_incident("Police 15.456.789 Fehler")

    assert decision.should_forward is True
    assert decision.target_team == "PKV"
    assert decision.continue_to_solution is False
    assert decision.detected_number == "15.456.789"
    assert decision.duty_calendar is not None
    assert decision.duty_calendar.url == "https://wiki.helvetia.group/x/l5GMK"
    assert decision.duty_calendar.duty_person is None
    assert decision.duty_calendar.status == "fallback_link_only"
    assert decision.snow_hint.affected_ci == "CH-heliX.NL-PKV"
    assert decision.snow_hint.service_offering == "CH-heliX.NL-PKV"


def test_offerte_16_routes_to_kmu_without_solution_continuation() -> None:
    decision = route_operational_incident("Offerte 16.001.456 blockiert")

    assert decision.should_forward is True
    assert decision.target_team == "KMU"
    assert decision.continue_to_solution is False
    assert decision.duty_calendar is not None
    assert decision.duty_calendar.url == "https://wiki.helvetia.group/x/W4mbvg"


def test_police_4005_routes_to_mf_and_continues() -> None:
    decision = route_operational_incident("Police 4.005.001.234 heliX-MF Fehler")

    assert decision.should_forward is False
    assert decision.target_team == "MF"
    assert decision.continue_to_solution is True



def test_routing_decision_serializes_nested_payloads() -> None:
    payload = route_operational_incident("Police 15.456.789 Fehler").to_dict()

    assert set(payload) == {
        "should_forward",
        "target_team",
        "route_reason",
        "detected_number",
        "snow_hint",
        "duty_calendar",
        "continue_to_solution",
    }
    assert payload["continue_to_solution"] is False
    assert isinstance(payload["snow_hint"], dict)
    assert isinstance(payload["duty_calendar"], dict)


def test_public_import_contract() -> None:
    assert IncidentRoutingDecision.__name__ == "IncidentRoutingDecision"
    assert route_operational_incident("unbekannt").continue_to_solution is True
