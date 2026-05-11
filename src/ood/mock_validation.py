from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


MOCK_REQUIRED_FIELDS = ("mock", "dataset", "synthetic_id")
VISIBLE_WARNING_PATTERN = re.compile(r"MOCK DATA.*SYNTHETIC|SYNTHETIC.*MOCK DATA", re.IGNORECASE | re.DOTALL)
GOLDEN_MARKERS = ("expected_answer", "expected_sources", "forbidden_sources", "golden")
SUSPICIOUS_PATTERNS: tuple[tuple[str, re.Pattern[str], str], ...] = (
    ("suspicious_email", re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "Replace real-looking email addresses with synthetic non-address labels."),
    ("suspicious_api_token", re.compile(r"\b(?:sk|api|token)[-_][A-Za-z0-9_-]{16,}\b", re.IGNORECASE), "Remove API-token-like strings; secrets must never be stored in Markdown."),
    ("suspicious_iban", re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"), "Replace IBAN-like values with synthetic IDs that start with MOCK-."),
    ("suspicious_phone", re.compile(r"(?:\+\d{1,3}[\s-]?)?(?:\d[\s-]?){8,}\d"), "Replace phone-number-like values with synthetic labels."),
    ("non_mock_identifier", re.compile(r"\b(?:INC\d{6,}|(?<!MOCK-)[A-Z]{2,10}-\d{2,})\b"), "Use synthetic identifiers prefixed with MOCK- for ServiceNow/Jira/ticket-like IDs."),
)


@dataclass(frozen=True)
class MockSafetyFinding:
    path: Path
    severity: str
    code: str
    message: str
    evidence: str

    def to_dict(self) -> dict[str, str]:
        return {
            "path": str(self.path),
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class MockCoverageSummary:
    source_types: dict[str, int]
    systems: dict[str, int]
    components: dict[str, int]
    routing_targets: dict[str, int]
    command_risks: dict[str, int]
    scenario_categories: dict[str, int]

    @classmethod
    def empty(cls) -> "MockCoverageSummary":
        return cls({}, {}, {}, {}, {}, {})

    def to_dict(self) -> dict[str, dict[str, int]]:
        return {
            "source_types": dict(sorted(self.source_types.items())),
            "systems": dict(sorted(self.systems.items())),
            "components": dict(sorted(self.components.items())),
            "routing_targets": dict(sorted(self.routing_targets.items())),
            "command_risks": dict(sorted(self.command_risks.items())),
            "scenario_categories": dict(sorted(self.scenario_categories.items())),
        }


@dataclass(frozen=True)
class MockValidationResult:
    corpus_dir: Path
    document_count: int
    findings: tuple[MockSafetyFinding, ...]
    coverage: MockCoverageSummary

    @property
    def is_safe(self) -> bool:
        return not any(finding.severity == "error" for finding in self.findings)

    def to_dict(self) -> dict[str, object]:
        return {
            "corpus_dir": str(self.corpus_dir),
            "document_count": self.document_count,
            "is_safe": self.is_safe,
            "findings": [finding.to_dict() for finding in self.findings],
            "coverage": self.coverage.to_dict(),
        }


def validate_mock_corpus(corpus_dir: Path) -> MockValidationResult:
    paths = sorted(corpus_dir.rglob("*.md"), key=lambda path: path.as_posix()) if corpus_dir.exists() else []
    findings: list[MockSafetyFinding] = []
    coverage = _CoverageBuilder()

    if not paths:
        findings.append(
            MockSafetyFinding(
                path=corpus_dir,
                severity="warning",
                code="empty_corpus",
                message="No Markdown files found. Add mock `.md` files or run `ood mock-init` for a starter corpus.",
                evidence=str(corpus_dir),
            )
        )
        return MockValidationResult(corpus_dir=corpus_dir, document_count=0, findings=tuple(findings), coverage=coverage.to_summary())

    for path in paths:
        content = path.read_text(encoding="utf-8")
        metadata, body = _split_frontmatter(content)
        findings.extend(_marker_findings(path, metadata, body))
        findings.extend(_suspicious_findings(path, content))
        findings.extend(_golden_findings(path, content))
        coverage.add(metadata)

    return MockValidationResult(corpus_dir=corpus_dir, document_count=len(paths), findings=tuple(findings), coverage=coverage.to_summary())


def _split_frontmatter(content: str) -> tuple[dict[str, str], str]:
    if not content.startswith("---\n"):
        return {}, content
    lines = content.splitlines()
    closing_index: int | None = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing_index = index
            break
    if closing_index is None:
        return {}, content
    metadata: dict[str, str] = {}
    for line in lines[1:closing_index]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip().strip("'\"")
        if key:
            metadata[key] = value
    return metadata, "\n".join(lines[closing_index + 1 :])


def _marker_findings(path: Path, metadata: dict[str, str], body: str) -> list[MockSafetyFinding]:
    findings: list[MockSafetyFinding] = []
    if metadata.get("mock") != "true":
        findings.append(_finding(path, "error", "missing_mock_true", "Add `mock: true` to YAML frontmatter so the file is visibly separated from real data.", "mock"))
    for field in ("dataset", "synthetic_id"):
        if not metadata.get(field):
            findings.append(_finding(path, "error", f"missing_{field}", f"Add `{field}` to YAML frontmatter for mock corpus traceability.", field))
    if not VISIBLE_WARNING_PATTERN.search(body[:300]):
        findings.append(_finding(path, "error", "missing_visible_warning", "Add a first body line containing MOCK DATA and SYNTHETIC before scenario content.", body[:80]))
    return findings


def _suspicious_findings(path: Path, content: str) -> list[MockSafetyFinding]:
    findings: list[MockSafetyFinding] = []
    for code, pattern, message in SUSPICIOUS_PATTERNS:
        for match in pattern.finditer(content):
            if code == "non_mock_identifier" and match.group(0).startswith("MOCK-"):
                continue
            findings.append(_finding(path, "error", code, message, match.group(0)))
            break
    return findings


def _golden_findings(path: Path, content: str) -> list[MockSafetyFinding]:
    lowered = content.lower()
    for marker in GOLDEN_MARKERS:
        if marker in lowered:
            return [_finding(path, "error", "golden_leakage", "Move expected answers/sources and golden labels to future evaluation JSON, never indexed Markdown.", marker)]
    return []


def _finding(path: Path, severity: str, code: str, message: str, evidence: str) -> MockSafetyFinding:
    return MockSafetyFinding(path=path, severity=severity, code=code, message=message, evidence=evidence)


class _CoverageBuilder:
    def __init__(self) -> None:
        self.source_types: dict[str, int] = {}
        self.systems: dict[str, int] = {}
        self.components: dict[str, int] = {}
        self.routing_targets: dict[str, int] = {}
        self.command_risks: dict[str, int] = {}
        self.scenario_categories: dict[str, int] = {}

    def add(self, metadata: dict[str, str]) -> None:
        self._increment(self.source_types, metadata.get("source_type"))
        self._increment(self.systems, metadata.get("system"))
        self._increment(self.components, metadata.get("komponente"))
        self._increment(self.routing_targets, metadata.get("routing_target"))
        self._increment(self.command_risks, metadata.get("command_risk"))
        self._increment(self.scenario_categories, metadata.get("scenario_category"))

    def to_summary(self) -> MockCoverageSummary:
        return MockCoverageSummary(
            source_types=dict(sorted(self.source_types.items())),
            systems=dict(sorted(self.systems.items())),
            components=dict(sorted(self.components.items())),
            routing_targets=dict(sorted(self.routing_targets.items())),
            command_risks=dict(sorted(self.command_risks.items())),
            scenario_categories=dict(sorted(self.scenario_categories.items())),
        )

    @staticmethod
    def _increment(counts: dict[str, int], value: str | None) -> None:
        if value:
            counts[value] = counts.get(value, 0) + 1


__all__ = ["MockCoverageSummary", "MockSafetyFinding", "MockValidationResult", "validate_mock_corpus"]
