from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SourceHit:
    """Stable source citation returned by OOD query operations."""

    path: str
    score: float
    excerpt: str
    score_details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the source hit without exposing retrieval-engine internals."""

        payload: dict[str, Any] = {
            "path": self.path,
            "score": self.score,
            "excerpt": self.excerpt,
        }
        if self.score_details:
            payload["score_details"] = self.score_details
        return payload


@dataclass(frozen=True)
class ConfidenceScore:
    """Heuristic confidence score plus user-facing rationale."""

    score: float
    rationale: str

    def to_dict(self) -> dict[str, str | float]:
        """Serialize confidence details for CLI JSON output."""

        return {
            "score": self.score,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class TicketIdentifier:
    """Context-aware ticket identifier; kind is "police" or "offerte"."""

    kind: str
    value: str
    confidence: float
    evidence: str

    def to_dict(self) -> dict[str, str | float]:
        return {
            "kind": self.kind,
            "value": self.value,
            "confidence": self.confidence,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class RoutingDecision:
    """Ticket route: selbst lösen, weiterleiten Policen, weiterleiten Offerten, or Rückfrage."""

    route: str
    rationale: str

    def to_dict(self) -> dict[str, str]:
        return {"route": self.route, "rationale": self.rationale}


@dataclass(frozen=True)
class CommandRisk:
    """Command risk label: grün, gelb, orange, or rot."""

    command: str
    risk: str
    rationale: str
    origin: str

    def to_dict(self) -> dict[str, str]:
        return {
            "command": self.command,
            "risk": self.risk,
            "rationale": self.rationale,
            "origin": self.origin,
        }


@dataclass(frozen=True)
class TicketAnalysis:
    """Structured ticket analysis with intent Problem, Frage, Request, or Unklar."""

    intent: str
    assessment: str | None
    solution_steps: list[str]
    routing: RoutingDecision
    identifiers: list[TicketIdentifier]
    command_risks: list[CommandRisk]
    uncertainties: list[str]
    mode: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "assessment": self.assessment,
            "solution_steps": self.solution_steps,
            "routing": self.routing.to_dict(),
            "identifiers": [identifier.to_dict() for identifier in self.identifiers],
            "command_risks": [risk.to_dict() for risk in self.command_risks],
            "uncertainties": self.uncertainties,
            "mode": self.mode,
        }


@dataclass(frozen=True)
class IndexResult:
    """Stable result for index and reindex operations."""

    status: str
    indexed_documents: int
    skipped_documents: int
    storage_dir: Path
    message: str
    metadata_warnings: list[MetadataWarning] = field(default_factory=list)
    duplicate_groups: list[DuplicateGroup] = field(default_factory=list)
    manifest_path: Path | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize index status with storage directory as a string."""

        payload: dict[str, Any] = {
            "status": self.status,
            "indexed_documents": self.indexed_documents,
            "skipped_documents": self.skipped_documents,
            "storage_dir": str(self.storage_dir),
            "message": self.message,
        }
        if self.metadata_warnings:
            payload["metadata_warnings"] = [warning.to_dict() for warning in self.metadata_warnings]
        if self.duplicate_groups:
            payload["duplicate_groups"] = [group.to_dict() for group in self.duplicate_groups]
        if self.manifest_path is not None:
            payload["manifest_path"] = str(self.manifest_path)
        return payload


@dataclass(frozen=True)
class MetadataWarning:
    """Warning-only metadata validation issue for a knowledge document."""

    path: str
    field: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"path": self.path, "field": self.field, "message": self.message}


@dataclass(frozen=True)
class DuplicateGroup:
    """Reporting-only exact or near duplicate knowledge group."""

    group_id: str
    kind: str
    canonical_path: str
    paths: list[str]
    score: float

    def to_dict(self) -> dict[str, object]:
        return {
            "group_id": self.group_id,
            "kind": self.kind,
            "canonical_path": self.canonical_path,
            "paths": self.paths,
            "score": self.score,
        }


@dataclass(frozen=True)
class ManifestEntry:
    """Manifest cache entry for one parsed Markdown knowledge document."""

    path: str
    content_hash: str
    body_hash: str
    metadata: dict[str, str]
    indexed_at: str
    warnings: list[MetadataWarning]
    body_excerpt: str
    duplicate_group_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "content_hash": self.content_hash,
            "body_hash": self.body_hash,
            "metadata": self.metadata,
            "indexed_at": self.indexed_at,
            "warnings": [warning.to_dict() for warning in self.warnings],
            "body_excerpt": self.body_excerpt,
            "duplicate_group_ids": self.duplicate_group_ids,
        }


@dataclass(frozen=True)
class ManifestDiff:
    """Hash-based diff between the current knowledge corpus and manifest."""

    new_paths: list[str]
    changed_paths: list[str]
    unchanged_paths: list[str]
    deleted_paths: list[str]
    skipped_paths: list[str]

    def to_dict(self) -> dict[str, list[str]]:
        return {
            "new_paths": self.new_paths,
            "changed_paths": self.changed_paths,
            "unchanged_paths": self.unchanged_paths,
            "deleted_paths": self.deleted_paths,
            "skipped_paths": self.skipped_paths,
        }


@dataclass(frozen=True)
class UpdateResult:
    """Stable result for incremental knowledge updates."""

    status: str
    indexed_documents: int
    skipped_documents: int
    storage_dir: Path
    manifest_path: Path
    message: str
    diff: ManifestDiff
    metadata_warnings: list[MetadataWarning]
    duplicate_groups: list[DuplicateGroup]
    schema_version: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "indexed_documents": self.indexed_documents,
            "skipped_documents": self.skipped_documents,
            "storage_dir": str(self.storage_dir),
            "manifest_path": str(self.manifest_path),
            "message": self.message,
            "diff": self.diff.to_dict(),
            "metadata_warnings": [warning.to_dict() for warning in self.metadata_warnings],
            "duplicate_groups": [group.to_dict() for group in self.duplicate_groups],
            "schema_version": self.schema_version,
        }


@dataclass(frozen=True)
class SourceScoreBreakdown:
    """Per-source retrieval score components for diagnostics and evaluation."""

    path: str
    semantic_score: float
    lexical_score: float
    combined_score: float
    lexical_matches: list[str]
    weights: dict[str, float]
    metadata_score: float = 0.0
    graph_score: float = 0.0
    final_score: float | None = None
    metadata_matches: list[str] = field(default_factory=list)
    graph_matches: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "semantic_score": self.semantic_score,
            "lexical_score": self.lexical_score,
            "metadata_score": self.metadata_score,
            "graph_score": self.graph_score,
            "combined_score": self.combined_score,
            "final_score": self.combined_score if self.final_score is None else self.final_score,
            "lexical_matches": self.lexical_matches,
            "metadata_matches": self.metadata_matches,
            "graph_matches": self.graph_matches,
            "weights": self.weights,
        }


@dataclass(frozen=True)
class RetrievalDiagnostics:
    """Stable public diagnostics for the retrieval backend and strategy."""

    backend: str = "unknown"
    strategy: str = "unknown"
    score_components: list[SourceScoreBreakdown] = field(default_factory=list)
    graph_retrieval: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "strategy": self.strategy,
            "score_components": [component.to_dict() for component in self.score_components],
            "graph_retrieval": self.graph_retrieval,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class IndexStatus:
    """Stable diagnostic status for configured knowledge and retrieval paths."""

    status: str
    knowledge_dir: Path
    data_dir: Path
    storage_dir: Path
    manifest_path: Path
    vector_index_path: Path
    knowledge_documents: int
    indexed_documents: int
    chunks: int
    storage_files: int
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "knowledge_dir": str(self.knowledge_dir),
            "data_dir": str(self.data_dir),
            "storage_dir": str(self.storage_dir),
            "manifest_path": str(self.manifest_path),
            "vector_index_path": str(self.vector_index_path),
            "knowledge_documents": self.knowledge_documents,
            "indexed_documents": self.indexed_documents,
            "chunks": self.chunks,
            "storage_files": self.storage_files,
            "message": self.message,
        }


@dataclass(frozen=True)
class QueryResult:
    """Stable result for query operations independent from LightRAG internals."""

    query: str
    answer: str | None
    confidence: ConfidenceScore
    sources: list[SourceHit]
    llm_used: bool
    status: str
    analysis: TicketAnalysis
    retrieval_diagnostics: RetrievalDiagnostics = field(default_factory=RetrievalDiagnostics)

    def to_dict(self) -> dict[str, Any]:
        """Serialize query results using the public OOD JSON contract."""

        return {
            "query": self.query,
            "answer": self.answer,
            "confidence": self.confidence.to_dict(),
            "sources": [source.to_dict() for source in self.sources],
            "llm_used": self.llm_used,
            "status": self.status,
            "analysis": self.analysis.to_dict(),
            "retrieval_diagnostics": self.retrieval_diagnostics.to_dict(),
        }


class IndexMissingError(RuntimeError):
    """Raised when a query runs before an index exists."""


__all__ = [
    "CommandRisk",
    "ConfidenceScore",
    "DuplicateGroup",
    "IndexMissingError",
    "IndexResult",
    "IndexStatus",
    "ManifestDiff",
    "ManifestEntry",
    "MetadataWarning",
    "QueryResult",
    "RoutingDecision",
    "RetrievalDiagnostics",
    "SourceHit",
    "SourceScoreBreakdown",
    "TicketAnalysis",
    "TicketIdentifier",
    "UpdateResult",
]
