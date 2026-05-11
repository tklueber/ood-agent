from __future__ import annotations

import re

from ood.models import CommandRisk, ConfidenceScore, RoutingDecision, SourceHit, TicketAnalysis, TicketIdentifier


PROBLEM_MARKERS = ("fehler", "stürzt ab", "geht nicht", "error", "failed", "failure", "kaputt")
QUESTION_MARKERS = ("wie", "warum", "?", "how", "why")
REQUEST_MARKERS = ("bitte", "kannst du", "please", "request", "einrichten", "anlegen")

POLICE_PATTERN = re.compile(r"\b(police|policennummer|policy)\s*[:#-]?\s*([A-Z]?-?\d{3,})\b", re.IGNORECASE)
OFFERTE_PATTERN = re.compile(r"\b(offerte|offertennummer|quote)\s*[:#-]?\s*([A-Z]?-?\d{3,})\b", re.IGNORECASE)

COMMAND_PATTERNS = (
    re.compile(r"\brm\s+-rf\s+[^\s,;]+", re.IGNORECASE),
    re.compile(r"\bdrop\s+database\s+[^\s,;]+", re.IGNORECASE),
    re.compile(r"\bdelete\s+from\s+[^\s,;]+", re.IGNORECASE),
    re.compile(r"\bchmod\s+777\s+[^\s,;]+", re.IGNORECASE),
    re.compile(r"\bsudo\s+[^,;.]+", re.IGNORECASE),
    re.compile(r"\bkubectl\s+delete\s+[^,;.]+", re.IGNORECASE),
    re.compile(r"\bterraform\s+destroy\b", re.IGNORECASE),
    re.compile(r"\bkubectl\s+get\s+[^,;.]+", re.IGNORECASE),
    re.compile(r"\bcurl\s+-I\s+[^\s,;]+", re.IGNORECASE),
    re.compile(r"\brestart\s+service\s+[^,;.]+", re.IGNORECASE),
    re.compile(r"\b(?:show|list|status|get)\b", re.IGNORECASE),
    re.compile(r"\b(?:retry|restart)\b(?:\s+[^,;.]+)?", re.IGNORECASE),
    re.compile(r"\b(?:update|set|write|deploy)\b(?:\s+[^,;.]+)?", re.IGNORECASE),
)


def analyze_ticket(ticket_text: str, sources: list[SourceHit], confidence: ConfidenceScore) -> TicketAnalysis:
    """Analyze ticket text and retrieved sources with deterministic local rules only."""

    intent = _classify_intent(ticket_text)
    identifiers = _extract_identifiers(ticket_text)
    uncertainties = _build_uncertainties(sources, confidence, intent)
    routing = _route_ticket(sources, confidence, identifiers)
    command_risks = _detect_command_risks(ticket_text, "ticket")
    for source in sources:
        command_risks.extend(_detect_command_risks(source.excerpt, source.path))

    return TicketAnalysis(
        intent=intent,
        assessment=None,
        solution_steps=[],
        routing=routing,
        identifiers=identifiers,
        command_risks=command_risks,
        uncertainties=uncertainties,
        mode="deterministic",
    )


def _classify_intent(ticket_text: str) -> str:
    text = ticket_text.lower()
    if any(marker in text for marker in QUESTION_MARKERS):
        return "Frage"
    if any(marker in text for marker in REQUEST_MARKERS):
        return "Request"
    if any(marker in text for marker in PROBLEM_MARKERS):
        return "Problem"
    return "Unklar"


def _extract_identifiers(ticket_text: str) -> list[TicketIdentifier]:
    identifiers: list[TicketIdentifier] = []
    for kind, pattern in (("police", POLICE_PATTERN), ("offerte", OFFERTE_PATTERN)):
        for match in pattern.finditer(ticket_text):
            value = match.group(2).upper()
            identifiers.append(
                TicketIdentifier(
                    kind=kind,
                    value=value,
                    confidence=0.9,
                    evidence=match.group(0).strip(),
                )
            )
    return identifiers


def _route_ticket(sources: list[SourceHit], confidence: ConfidenceScore, identifiers: list[TicketIdentifier]) -> RoutingDecision:
    if not sources:
        return RoutingDecision(route="Rückfrage", rationale="Keine belastbaren Quellen gefunden.")
    if confidence.score < 0.5:
        return RoutingDecision(route="Rückfrage", rationale="Niedrige Retrieval-Confidence.")

    kinds = {identifier.kind for identifier in identifiers}
    if kinds == {"police", "offerte"}:
        return RoutingDecision(route="Rückfrage", rationale="Police- und Offerten-Kontext gemischt.")
    if "police" in kinds:
        return RoutingDecision(route="weiterleiten Policen", rationale="Police context")
    if "offerte" in kinds:
        return RoutingDecision(route="weiterleiten Offerten", rationale="Offerte context")
    return RoutingDecision(route="selbst lösen", rationale="Actionable source with sufficient confidence.")


def _build_uncertainties(sources: list[SourceHit], confidence: ConfidenceScore, intent: str) -> list[str]:
    uncertainties: list[str] = []
    if not sources:
        uncertainties.append("Keine belastbaren Quellen gefunden.")
    if confidence.score < 0.5:
        uncertainties.append("Niedrige Retrieval-Confidence.")
    if intent == "Unklar":
        uncertainties.append("Intent nicht eindeutig.")
    return uncertainties


def _detect_command_risks(text: str, origin: str) -> list[CommandRisk]:
    risks: list[CommandRisk] = []
    seen: set[str] = set()
    for pattern in COMMAND_PATTERNS:
        for match in pattern.finditer(text):
            command = match.group(0).strip().rstrip(".,")
            normalized = command.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            risk, rationale = _classify_command(command)
            risks.append(CommandRisk(command=command, risk=risk, rationale=rationale, origin=origin))
    return risks


def _classify_command(command: str) -> tuple[str, str]:
    text = command.lower()
    if any(marker in text for marker in ("rm -rf", "drop database", "delete from", "chmod 777", "sudo", "kubectl delete", "terraform destroy")):
        return "rot", "Destructive, privileged, or security-sensitive command."
    if "restart service" in text or any(marker in text for marker in ("update", "set", "write", "deploy")):
        return "orange", "State, configuration, or service-changing command."
    if any(marker in text for marker in ("restart", "retry")):
        return "gelb", "Reversible low-impact operational action."
    if any(text.startswith(marker) for marker in ("show", "list", "status", "get", "curl -i", "kubectl get")):
        return "grün", "Read-only diagnostic command."
    return "orange", "Unknown shell-like command; conservative risk escalation."


__all__ = ["analyze_ticket"]
