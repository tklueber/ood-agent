from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


CALENDAR_URLS = {
    "PKV": "https://wiki.helvetia.group/x/l5GMK",
    "KMU": "https://wiki.helvetia.group/x/W4mbvg",
    "MF": "https://wiki.helvetia.group/x/TIElfQ",
}

SNOW_HINTS = {
    "PKV": ("CH-heliX.NL-PKV", "CH-heliX.NL-PKV", None),
    "KMU": ("CH-heliX.NL-KMU", "CH-heliX.NL-KMU", None),
    "MF": ("CH-heliX.Frontend.MF", "CH-heliX.Frontend.MF", None),
}

INCIDENT_NUMBER_PATTERN = re.compile(r"\b(?:police|offerte|policy|quote)?\s*([0-9]+\.[0-9]{3}\.[0-9.]+)\b", re.IGNORECASE)


@dataclass(frozen=True)
class DutyCalendar:
    area: str
    url: str
    duty_person: str | None
    status: str

    def to_dict(self) -> dict[str, str | None]:
        return {
            "area": self.area,
            "url": self.url,
            "duty_person": self.duty_person,
            "status": self.status,
        }


@dataclass(frozen=True)
class SnowAssignmentHint:
    affected_ci: str | None
    service_offering: str | None
    assignment_group: str | None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "affected_ci": self.affected_ci,
            "service_offering": self.service_offering,
            "assignment_group": self.assignment_group,
        }


@dataclass(frozen=True)
class IncidentRoutingDecision:
    should_forward: bool
    target_team: str | None
    route_reason: str
    detected_number: str | None
    snow_hint: SnowAssignmentHint
    duty_calendar: DutyCalendar | None
    continue_to_solution: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "should_forward": self.should_forward,
            "target_team": self.target_team,
            "route_reason": self.route_reason,
            "detected_number": self.detected_number,
            "snow_hint": self.snow_hint.to_dict(),
            "duty_calendar": self.duty_calendar.to_dict() if self.duty_calendar else None,
            "continue_to_solution": self.continue_to_solution,
        }


def _calendar(area: str) -> DutyCalendar:
    return DutyCalendar(area=area, url=CALENDAR_URLS[area], duty_person=None, status="fallback_link_only")


def _snow(area: str | None) -> SnowAssignmentHint:
    if area is None:
        return SnowAssignmentHint(affected_ci=None, service_offering=None, assignment_group=None)
    affected_ci, service_offering, assignment_group = SNOW_HINTS.get(area, (None, None, None))
    return SnowAssignmentHint(affected_ci=affected_ci, service_offering=service_offering, assignment_group=assignment_group)


def route_operational_incident(ticket_text: str) -> IncidentRoutingDecision:
    """Route operational incidents before any retrieval or Cloud LLM work occurs."""

    match = INCIDENT_NUMBER_PATTERN.search(ticket_text)
    number = match.group(1) if match else None

    if number is None:
        return IncidentRoutingDecision(
            should_forward=False,
            target_team=None,
            route_reason="Keine Policen-/Offertennummer erkannt; OOD bearbeitet weiter.",
            detected_number=None,
            snow_hint=_snow(None),
            duty_calendar=None,
            continue_to_solution=True,
        )

    if number.startswith("15."):
        return IncidentRoutingDecision(True, "PKV", "Präfix 15.* wird an PKV weitergeleitet.", number, _snow("PKV"), _calendar("PKV"), False)
    if number.startswith("16."):
        return IncidentRoutingDecision(True, "KMU", "Präfix 16.* wird an KMU weitergeleitet.", number, _snow("KMU"), _calendar("KMU"), False)
    if number.startswith(("4.000.", "4.001.")):
        return IncidentRoutingDecision(True, "PKV/KMU", "Präfix 4.000./4.001. benötigt Spartenklärung vor Weiterleitung.", number, _snow(None), None, False)
    if number.startswith(("4.005.", "4.007.")):
        return IncidentRoutingDecision(False, "MF", "MF-Präfix; OOD setzt Lösungssuche fort.", number, _snow("MF"), _calendar("MF"), True)
    if number.startswith("4.008."):
        return IncidentRoutingDecision(False, "MF/other", "Präfix 4.008. ist spartenunsicher; OOD setzt mit Unsicherheit fort.", number, _snow(None), None, True)
    return IncidentRoutingDecision(False, None, "Nummer erkannt, aber kein Weiterleitungspräfix; OOD bearbeitet weiter.", number, _snow(None), None, True)


__all__ = ["DutyCalendar", "SnowAssignmentHint", "IncidentRoutingDecision", "route_operational_incident"]
