from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class QualityIssue:
    path: str
    code: str
    severity: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"path": self.path, "code": self.code, "severity": self.severity, "message": self.message}


@dataclass(frozen=True)
class QualityRecommendation:
    severity: str
    reason: str
    suggestion: str
    path: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {"severity": self.severity, "path": self.path, "reason": self.reason, "suggestion": self.suggestion}


@dataclass(frozen=True)
class FieldCoverage:
    field: str
    present: int
    total: int

    @property
    def ratio(self) -> float:
        return round(self.present / self.total, 4) if self.total else 0.0

    def to_dict(self) -> dict[str, str | int | float]:
        return {"field": self.field, "present": self.present, "total": self.total, "ratio": self.ratio}


@dataclass(frozen=True)
class KnowledgeQualityReport:
    corpus_dir: Path
    document_count: int
    expected_documents: int | None
    expected_document_mismatch: bool
    readiness_score: float
    field_coverage: dict[str, FieldCoverage]
    link_counts: dict[str, int]
    command_coverage: dict[str, int]
    freshness: dict[str, int]
    duplicates: dict[str, list[dict[str, Any]]]
    source_attribution: dict[str, int]
    document_issues: list[QualityIssue] = field(default_factory=list)
    recommendations: list[QualityRecommendation] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "corpus_dir": str(self.corpus_dir),
            "document_count": self.document_count,
            "expected_documents": self.expected_documents,
            "expected_document_mismatch": self.expected_document_mismatch,
            "readiness_score": self.readiness_score,
            "field_coverage": {key: coverage.to_dict() for key, coverage in self.field_coverage.items()},
            "link_counts": self.link_counts,
            "command_coverage": self.command_coverage,
            "freshness": self.freshness,
            "duplicates": self.duplicates,
            "source_attribution": self.source_attribution,
            "document_issues": [issue.to_dict() for issue in self.document_issues],
            "recommendations": [recommendation.to_dict() for recommendation in self.recommendations],
        }


@dataclass(frozen=True)
class _DocumentAudit:
    path: str
    metadata: dict[str, object]
    body: str
    links: list[str]
    commands: list[str]
    has_risk_marker: bool


def audit_knowledge_corpus(corpus_dir: Path, *, expected_documents: int | None = None) -> KnowledgeQualityReport:
    documents = [_parse_document(path, corpus_dir) for path in sorted(corpus_dir.rglob("*.md"), key=lambda item: item.as_posix())] if corpus_dir.exists() else []
    total = len(documents)
    if total == 0:
        recommendation = QualityRecommendation(
            severity="warning",
            path=None,
            reason="No Markdown documents found in corpus.",
            suggestion="Export or point --corpus-dir at the OOD-KB articles directory before running retrieval quality review.",
        )
        return KnowledgeQualityReport(
            corpus_dir=corpus_dir,
            document_count=0,
            expected_documents=expected_documents,
            expected_document_mismatch=expected_documents not in (None, 0),
            readiness_score=0.0,
            field_coverage={},
            link_counts={"outgoing": 0, "incoming": 0, "documents_with_links": 0},
            command_coverage={"documents_with_commands": 0, "documents_with_risk_marker": 0},
            freshness={"documents_with_freshness": 0, "stale_documents": 0},
            duplicates={"titles": [], "kb_ids": []},
            source_attribution={"documents_with_source": 0},
            recommendations=[recommendation],
        )

    coverage_keys = ["title", "type", "service_or_system", "keywords", "freshness", "owner", "aliases", "related"]
    field_coverage = {
        key: FieldCoverage(key, sum(1 for doc in documents if _has_field(doc, key)), total) for key in coverage_keys
    }
    outgoing_links = sum(len(doc.links) for doc in documents)
    link_targets = {slug for doc in documents for slug in doc.links}
    incoming = sum(1 for doc in documents if _slug(Path(doc.path).stem) in link_targets)
    command_docs = sum(1 for doc in documents if doc.commands)
    risk_docs = sum(1 for doc in documents if doc.has_risk_marker)
    stale_docs = sum(1 for doc in documents if _is_stale(doc.metadata.get("last_verified") or doc.metadata.get("last_synced")))
    freshness_docs = sum(1 for doc in documents if doc.metadata.get("last_verified") or doc.metadata.get("last_synced"))
    source_docs = sum(1 for doc in documents if any(doc.metadata.get(key) for key in ("confluence_url", "snow_incidents", "jira", "quelle")))
    duplicates = {
        "titles": _duplicate_values(documents, "title"),
        "kb_ids": _duplicate_values(documents, "kb_id"),
    }
    issues: list[QualityIssue] = []
    recommendations: list[QualityRecommendation] = []
    for doc in documents:
        _extend_document_findings(doc, issues, recommendations)
    _extend_corpus_recommendations(field_coverage, outgoing_links, command_docs, source_docs, total, recommendations)
    for group in duplicates["titles"]:
        recommendations.append(QualityRecommendation("warning", f"Duplicate title: {group['value']}", "Make titles unique enough for retrieval snippets and operator scanning."))
    for group in duplicates["kb_ids"]:
        recommendations.append(QualityRecommendation("warning", f"Duplicate kb_id: {group['value']}", "Keep kb_id values unique or remove stale copies to avoid source ambiguity."))
    readiness = round(
        sum(coverage.ratio for coverage in field_coverage.values()) / len(field_coverage) * 0.75
        + min(1.0, outgoing_links / max(1, total)) * 0.10
        + min(1.0, command_docs / max(1, total)) * 0.05
        + min(1.0, source_docs / max(1, total)) * 0.10,
        4,
    )
    return KnowledgeQualityReport(
        corpus_dir=corpus_dir,
        document_count=total,
        expected_documents=expected_documents,
        expected_document_mismatch=expected_documents is not None and expected_documents != total,
        readiness_score=readiness,
        field_coverage=field_coverage,
        link_counts={"outgoing": outgoing_links, "incoming": incoming, "documents_with_links": sum(1 for doc in documents if doc.links)},
        command_coverage={"documents_with_commands": command_docs, "documents_with_risk_marker": risk_docs},
        freshness={"documents_with_freshness": freshness_docs, "stale_documents": stale_docs},
        duplicates=duplicates,
        source_attribution={"documents_with_source": source_docs},
        document_issues=issues,
        recommendations=recommendations,
    )


def _parse_document(path: Path, corpus_dir: Path) -> _DocumentAudit:
    raw = path.read_text(encoding="utf-8")
    metadata, body = _split_frontmatter(raw)
    relative_path = path.relative_to(corpus_dir).as_posix()
    return _DocumentAudit(
        path=relative_path,
        metadata=metadata,
        body=body,
        links=[match.group(1).split("|", 1)[0].strip() for match in re.finditer(r"\[\[([^\]]+)\]\]", body)],
        commands=_extract_commands(body, metadata),
        has_risk_marker=bool(re.search(r"risk\s*:\s*(grün|gelb|orange|rot|green|yellow|red)", body, re.IGNORECASE)),
    )


def _split_frontmatter(content: str) -> tuple[dict[str, object], str]:
    if not content.startswith("---\n"):
        return {}, content
    lines = content.splitlines()
    closing = next((index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"), None)
    if closing is None:
        return {}, content
    metadata: dict[str, object] = {}
    current_key: str | None = None
    for line in lines[1:closing]:
        stripped = line.strip()
        if stripped.startswith("-") and current_key:
            values = metadata.setdefault(current_key, [])
            if isinstance(values, list):
                values.append(stripped[1:].strip().strip("'\""))
            continue
        if ":" not in line:
            current_key = None
            continue
        key, value = line.split(":", 1)
        current_key = key.strip().lower()
        cleaned = value.strip().strip("'\"")
        if cleaned.startswith("[") and cleaned.endswith("]"):
            metadata[current_key] = [part.strip().strip("'\"") for part in cleaned[1:-1].split(",") if part.strip()]
        elif cleaned:
            metadata[current_key] = cleaned
        else:
            metadata[current_key] = []
    return metadata, "\n".join(lines[closing + 1 :])


def _has_field(doc: _DocumentAudit, key: str) -> bool:
    if key == "service_or_system":
        return bool(doc.metadata.get("service") or doc.metadata.get("system"))
    if key == "keywords":
        return any(doc.metadata.get(name) for name in ("keywords", "keywords_de", "keywords_en"))
    if key == "freshness":
        return bool(doc.metadata.get("last_verified") or doc.metadata.get("last_synced"))
    value = doc.metadata.get(key)
    return bool(value)


def _values(metadata: dict[str, object], *keys: str) -> list[str]:
    output: list[str] = []
    for key in keys:
        value = metadata.get(key)
        if isinstance(value, list):
            output.extend(str(item) for item in value if str(item).strip())
        elif isinstance(value, str) and value.strip():
            output.append(value)
    return output


def _extract_commands(body: str, metadata: dict[str, object]) -> list[str]:
    commands = _values(metadata, "splunk_queries")
    in_commands = False
    in_fence = False
    for line in body.splitlines():
        stripped = line.strip()
        if re.match(r"^#{1,6}\s+", stripped):
            in_commands = "command" in stripped.lower()
            continue
        if not in_commands:
            continue
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence and stripped:
            commands.append(stripped)
    return commands


def _is_stale(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        parsed = date.fromisoformat(value[:10])
    except ValueError:
        return True
    return parsed < date(2025, 1, 1)


def _duplicate_values(documents: list[_DocumentAudit], key: str) -> list[dict[str, Any]]:
    values: dict[str, list[str]] = {}
    for doc in documents:
        value = doc.metadata.get(key)
        if isinstance(value, str) and value.strip():
            values.setdefault(value, []).append(doc.path)
    return [{"value": value, "paths": paths} for value, paths in sorted(values.items()) if len(paths) > 1]


def _extend_document_findings(doc: _DocumentAudit, issues: list[QualityIssue], recommendations: list[QualityRecommendation]) -> None:
    required = ["title", "type", "last_verified", "owner", "aliases", "related"]
    if not (doc.metadata.get("service") or doc.metadata.get("system")):
        required.append("system")
    if not (doc.metadata.get("component") or doc.metadata.get("komponente")):
        required.append("component")
    if not any(doc.metadata.get(name) for name in ("keywords", "keywords_de", "keywords_en")):
        required.append("keywords")
    for field_name in required:
        if not doc.metadata.get(field_name):
            issues.append(QualityIssue(doc.path, f"missing_{field_name}", "warning", f"Missing {field_name} metadata."))
            recommendations.append(
                QualityRecommendation(
                    severity="warning",
                    path=doc.path,
                    reason=f"Missing normalized `{field_name}` metadata.",
                    suggestion=f"Add `{field_name}` frontmatter so metadata/graph retrieval can explain matches.",
                )
            )
    if not doc.links:
        recommendations.append(QualityRecommendation("info", "Document has no Wikilinks.", "Add `related` frontmatter or Obsidian Wikilinks to tickets, runbooks, and error-code notes.", doc.path))
    if doc.commands and not doc.has_risk_marker:
        recommendations.append(QualityRecommendation("warning", "Command block has no risk marker.", "Add command risk markers (`grün`, `gelb`, `orange`, `rot`) near executable snippets.", doc.path))
    if not any(doc.metadata.get(key) for key in ("confluence_url", "snow_incidents", "jira", "quelle")):
        recommendations.append(QualityRecommendation("info", "Missing source attribution.", "Add `quelle`, `confluence_url`, `snow_incidents`, or `jira` references for trust and follow-up.", doc.path))
    text = " ".join([doc.path, doc.body, *map(str, doc.metadata.values())]).lower()
    if "traceid" in text or "kafka" in text or "akhq" in text:
        recommendations.append(
            QualityRecommendation(
                "warning",
                "TraceId/Kafka signals need normalized synonyms and relationships.",
                "Add aliases/synonyms: `trace id`, `traceid`, `TraceId`, `correlation id`, `Kafka message`, `AKHQ`, `Ersatzgeschäft`; also add `system: AKHQ`, `component`, `related`, `last_verified`, and `owner`.",
                doc.path,
            )
        )


def _extend_corpus_recommendations(
    field_coverage: dict[str, FieldCoverage],
    outgoing_links: int,
    command_docs: int,
    source_docs: int,
    total: int,
    recommendations: list[QualityRecommendation],
) -> None:
    if field_coverage["keywords"].ratio < 0.8:
        recommendations.append(QualityRecommendation("warning", "Low keyword coverage.", "Add keywords/keywords_de/keywords_en to improve metadata retrieval and synonym matching."))
    if field_coverage["service_or_system"].ratio < 0.8:
        recommendations.append(QualityRecommendation("warning", "Low service/system coverage.", "Add normalized service/system fields and component/problem_type metadata to every operational article."))
    if outgoing_links < total:
        recommendations.append(QualityRecommendation("info", "Sparse Wikilink graph.", "Link troubleshooting articles to tickets, runbooks, system notes, and error-code pages with Obsidian Wikilinks."))
    if command_docs == 0:
        recommendations.append(QualityRecommendation("info", "No command examples detected.", "Use `## Commands` sections with risk markers when articles include operational checks."))
    if source_docs < total:
        recommendations.append(QualityRecommendation("info", "Incomplete source attribution.", "Add source attribution fields (`quelle`, `confluence_url`, `snow_incidents`, `jira`) for auditability."))


def _slug(value: str) -> str:
    return re.sub(r"[^\wÄÖÜäöüß]+", "-", value.lower()).strip("-")


__all__ = [
    "FieldCoverage",
    "KnowledgeQualityReport",
    "QualityIssue",
    "QualityRecommendation",
    "audit_knowledge_corpus",
]
