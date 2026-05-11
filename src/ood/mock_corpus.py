from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


PHASE5_MOCK_DATE = "2026-05-03"
MOCK_WARNING = "⚠️ MOCK DATA / SYNTHETIC: Dieses Dokument ist vollständig künstlich erzeugt und enthält keine Produktionsdaten."


@dataclass(frozen=True)
class MockDocument:
    path: Path
    title: str
    source_type: str
    system: str
    komponente: str
    scenario_category: str
    routing_target: str
    command_risk: str
    synthetic_id: str
    tags: tuple[str, ...]
    body: str

    def to_markdown(self, *, dataset: str = "mock-v1") -> str:
        frontmatter = {
            "mock": "true",
            "dataset": dataset,
            "synthetic_id": self.synthetic_id,
            "source_type": self.source_type,
            "scenario_category": self.scenario_category,
            "routing_target": self.routing_target,
            "command_risk": self.command_risk,
            "tags": ", ".join(self.tags),
            "quelle": "OOD synthetic mock corpus",
            "datum": PHASE5_MOCK_DATE,
            "status": "active",
            "system": self.system,
            "komponente": self.komponente,
            "title": self.title,
            "type": self.source_type,
        }
        lines = ["---", *(f"{key}: {value}" for key, value in frontmatter.items()), "---", MOCK_WARNING, "", self.body.strip(), ""]
        return "\n".join(lines)


@dataclass(frozen=True)
class MockCorpusResult:
    dataset: str
    target_dir: Path
    generated_paths: tuple[Path, ...]
    source_types: tuple[str, ...]

    @property
    def document_count(self) -> int:
        return len(self.generated_paths)

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset": self.dataset,
            "target_dir": str(self.target_dir),
            "document_count": self.document_count,
            "generated_paths": [str(path) for path in self.generated_paths],
            "source_types": list(self.source_types),
        }


def generate_mock_corpus(target_dir: Path, *, dataset: str = "mock-v1") -> MockCorpusResult:
    documents = _mock_documents(target_dir)
    generated_paths: list[Path] = []
    for document in documents:
        document.path.parent.mkdir(parents=True, exist_ok=True)
        document.path.write_text(document.to_markdown(dataset=dataset), encoding="utf-8")
        generated_paths.append(document.path)

    return MockCorpusResult(
        dataset=dataset,
        target_dir=target_dir,
        generated_paths=tuple(generated_paths),
        source_types=tuple(sorted({document.source_type for document in documents})),
    )


def _mock_documents(target_dir: Path) -> tuple[MockDocument, ...]:
    specs = (
        ("ticket", "MOCK-POL-1001", "Police Login Timeout", "Bestand", "Police Login", "login_timeout", "weiterleiten Policen", "gelb", "Nutzer meldet, dass die synthetische Police MOCK-POL-1001 beim Login in der Teststrecke nach 30 Sekunden abbricht. Prüfen: Session zurücksetzen, Browsercache leeren, danach erneuter Login im Mock-Mandanten."),
        ("ticket", "MOCK-OFF-2001", "Offerte bleibt im Entwurf", "Offerten", "Angebotsworkflow", "draft_stuck", "weiterleiten Offerten", "grün", "Eine fiktive Offerte MOCK-OFF-2001 bleibt im Status Entwurf. Der bekannte Workaround ist eine Statusaktualisierung im Mock-Workflow und erneutes Speichern ohne Produktivverbindung."),
        ("servicenow_case", "MOCK-SNOW-3001", "ServiceNow Case zur Batch-Verzögerung", "ServiceNow", "Incident Routing", "batch_delay", "Rückfrage", "gelb", "Der synthetische ServiceNow-Fall MOCK-SNOW-3001 beschreibt verspätete Batch-Verarbeitung. Vor Routing sollen System, Uhrzeit und betroffener Mock-Mandant nachgefragt werden."),
        ("servicenow_case", "MOCK-SNOW-3002", "Case: Dokumentenversand fehlerhaft", "DMS", "Versandqueue", "document_delivery", "selbst lösen", "orange", "Im Mock-Case staut sich der Dokumentenversand. Operatoren prüfen Queue-Zustand und starten nur freigegebene Test-Jobs neu; keine produktiven Versandläufe auslösen."),
        ("jira_bug", "MOCK-JIRA-4001", "Jira Bug: Fehlende Fehlermeldung", "Portal", "Frontend", "ui_error_message", "weiterleiten Offerten", "grün", "Der synthetische Jira-Bug MOCK-JIRA-4001 dokumentiert eine fehlende Fehlermeldung bei ungültigen Offertendaten. Reproduktion erfolgt ausschließlich mit Mock-Datensätzen."),
        ("jira_bug", "MOCK-JIRA-4002", "Jira Bug: Worker retry loop", "Bestand", "Worker", "retry_loop", "weiterleiten Policen", "orange", "Ein Test-Worker verarbeitet MOCK-POL-1002 mehrfach. Empfohlen ist Logprüfung, Sperrprüfung und Weitergabe an Policen, falls der Retry-Zähler weiter steigt."),
        ("wiki", "MOCK-WIKI-5001", "Wiki: Police Login Diagnose", "Bestand", "Police Login", "diagnostic_guide", "selbst lösen", "grün", "Dieser synthetische Wiki-Artikel beschreibt die Diagnose für Login-Timeouts: Sessionstatus prüfen, bekannte Wartungsfenster abgleichen, Kundenauswirkung im Mock-Ticket dokumentieren."),
        ("wiki", "MOCK-WIKI-5002", "Wiki: Offerten Routingregeln", "Offerten", "Routing", "routing_policy", "weiterleiten Offerten", "grün", "Die Mock-Routingregel besagt: Offerten mit blockiertem Angebotsworkflow gehen an das Offerten-Team, außer die Beschreibung enthält unklare Systemangaben."),
        ("runbook", "MOCK-RUN-6001", "Runbook: Versandqueue prüfen", "DMS", "Versandqueue", "queue_check", "selbst lösen", "orange", "Runbook für synthetische Versandqueues: Status anzeigen, blockierte Mock-Jobs identifizieren, Änderungsfenster prüfen und nur explizit freigegebene Test-Neustarts durchführen."),
        ("runbook", "MOCK-RUN-6002", "Runbook: Batch-Verzögerung triagieren", "Batch", "Nachtlauf", "batch_delay", "Rückfrage", "gelb", "Bei synthetischer Batch-Verzögerung werden Lauf-ID, Zeitraum und betroffene Mock-Komponente gesammelt. Ohne diese Angaben ist eine Rückfrage erforderlich."),
        ("note", "MOCK-NOTE-7001", "Notiz: Häufige Login-Verwechslung", "Bestand", "Police Login", "operator_note", "selbst lösen", "grün", "Interne synthetische Notiz: Viele Mock-Tickets nennen Loginfehler, meinen aber abgelaufene Test-Sessions. Erst Session erneuern, dann weitere Analyse."),
        ("note", "MOCK-NOTE-7002", "Notiz: Rote Befehle vermeiden", "Plattform", "Betrieb", "command_safety", "Rückfrage", "rot", "Synthetische Sicherheitshinweise: destruktive oder privilegierte Kommandos werden in OOD nur klassifiziert. Operatoren führen keine ungeprüften Befehle aus."),
    )
    documents: list[MockDocument] = []
    for source_type, synthetic_id, title, system, komponente, scenario, routing, risk, body in specs:
        slug = synthetic_id.lower().replace("_", "-")
        documents.append(
            MockDocument(
                path=target_dir / source_type / f"{slug}.md",
                title=title,
                source_type=source_type,
                system=system,
                komponente=komponente,
                scenario_category=scenario,
                routing_target=routing,
                command_risk=risk,
                synthetic_id=synthetic_id,
                tags=("mock", source_type, scenario),
                body=f"# {title}\n\n{body}\n\nSynthetische Referenz: {synthetic_id}.",
            )
        )
    return tuple(documents)


__all__ = ["MockCorpusResult", "MockDocument", "generate_mock_corpus"]
