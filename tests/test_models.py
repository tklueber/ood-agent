from pathlib import Path

from ood.models import (
    CommandRisk,
    ConfidenceScore,
    DuplicateGroup,
    IndexResult,
    ManifestDiff,
    ManifestEntry,
    MetadataWarning,
    QueryResult,
    RetrievalDiagnostics,
    RoutingDecision,
    SourceHit,
    SourceScoreBreakdown,
    TicketAnalysis,
    TicketIdentifier,
    UpdateResult,
)


def test_source_hit_to_dict_matches_json_contract() -> None:
    source = SourceHit(path="runbook.md", score=0.87, excerpt="restart service")

    assert source.to_dict() == {
        "path": "runbook.md",
        "score": 0.87,
        "excerpt": "restart service",
    }


def test_source_score_breakdown_serializes_metadata_graph_defaults() -> None:
    breakdown = SourceScoreBreakdown(
        path="runbook.md",
        semantic_score=0.4,
        lexical_score=0.5,
        combined_score=0.6,
        lexical_matches=["traceid"],
        weights={"semantic": 0.45},
    )

    assert breakdown.to_dict() == {
        "path": "runbook.md",
        "semantic_score": 0.4,
        "lexical_score": 0.5,
        "metadata_score": 0.0,
        "graph_score": 0.0,
        "combined_score": 0.6,
        "final_score": 0.6,
        "lexical_matches": ["traceid"],
        "metadata_matches": [],
        "graph_matches": [],
        "weights": {"semantic": 0.45},
    }


def test_query_result_serializes_extended_score_components() -> None:
    result = QueryResult(
        query="TraceId Kafka",
        answer=None,
        confidence=ConfidenceScore(score=0.8, rationale="Hybrid confidence."),
        sources=[SourceHit(path="how-to.md", score=0.9, excerpt="TraceId in Kafka")],
        llm_used=False,
        status="success",
        analysis=TicketAnalysis(
            intent="Frage",
            assessment=None,
            solution_steps=[],
            routing=RoutingDecision(route="selbst lösen", rationale="Actionable source"),
            identifiers=[],
            command_risks=[],
            uncertainties=[],
            mode="deterministic",
        ),
        retrieval_diagnostics=RetrievalDiagnostics(
            score_components=[
                SourceScoreBreakdown(
                    path="how-to.md",
                    semantic_score=0.1,
                    lexical_score=0.2,
                    combined_score=0.3,
                    lexical_matches=["kafka"],
                    weights={"metadata": 0.2},
                    metadata_score=0.9,
                    graph_score=0.7,
                    final_score=0.88,
                    metadata_matches=["keyword:TraceId"],
                    graph_matches=["incoming_link:ticket.md"],
                )
            ]
        ),
    )

    component = result.to_dict()["retrieval_diagnostics"]["score_components"][0]
    assert component["metadata_score"] == 0.9
    assert component["graph_score"] == 0.7
    assert component["final_score"] == 0.88
    assert component["metadata_matches"] == ["keyword:TraceId"]
    assert component["graph_matches"] == ["incoming_link:ticket.md"]


def test_confidence_score_to_dict_matches_json_contract() -> None:
    confidence = ConfidenceScore(score=0.42, rationale="retrieval-only: 1 source")

    assert confidence.to_dict() == {
        "score": 0.42,
        "rationale": "retrieval-only: 1 source",
    }


def test_query_result_to_dict_matches_json_contract() -> None:
    result = QueryResult(
        query="How do I fix the incident?",
        answer=None,
        confidence=ConfidenceScore(score=0.42, rationale="retrieval-only: 1 source"),
        sources=[SourceHit(path="runbook.md", score=0.87, excerpt="restart service")],
        llm_used=False,
        status="success",
        analysis=TicketAnalysis(
            intent="Problem",
            assessment=None,
            solution_steps=[],
            routing=RoutingDecision(route="selbst lösen", rationale="Actionable source"),
            identifiers=[],
            command_risks=[],
            uncertainties=[],
            mode="deterministic",
        ),
    )

    assert result.to_dict() == {
        "query": "How do I fix the incident?",
        "answer": None,
        "confidence": {
            "score": 0.42,
            "rationale": "retrieval-only: 1 source",
        },
        "sources": [
            {
                "path": "runbook.md",
                "score": 0.87,
                "excerpt": "restart service",
            }
        ],
        "llm_used": False,
        "status": "success",
        "analysis": {
            "intent": "Problem",
            "assessment": None,
            "solution_steps": [],
            "routing": {"route": "selbst lösen", "rationale": "Actionable source"},
            "identifiers": [],
            "command_risks": [],
            "uncertainties": [],
            "mode": "deterministic",
        },
        "retrieval_diagnostics": {
            "backend": "unknown",
            "strategy": "unknown",
            "score_components": [],
            "graph_retrieval": {},
            "notes": [],
        },
    }


def test_ticket_analysis_models_serialize_nested_json_contract() -> None:
    identifier = TicketIdentifier(kind="police", value="P-12345", confidence=0.9, evidence="Police P-12345")
    routing = RoutingDecision(route="weiterleiten Policen", rationale="Police context")
    risk = CommandRisk(command="rm -rf /tmp/x", risk="rot", rationale="Destructive delete", origin="ticket")
    analysis = TicketAnalysis(
        intent="Problem",
        assessment=None,
        solution_steps=[],
        routing=routing,
        identifiers=[identifier],
        command_risks=[risk],
        uncertainties=["Niedrige Retrieval-Confidence."],
        mode="deterministic",
    )

    assert identifier.to_dict() == {
        "kind": "police",
        "value": "P-12345",
        "confidence": 0.9,
        "evidence": "Police P-12345",
    }
    assert routing.to_dict() == {"route": "weiterleiten Policen", "rationale": "Police context"}
    assert risk.to_dict() == {
        "command": "rm -rf /tmp/x",
        "risk": "rot",
        "rationale": "Destructive delete",
        "origin": "ticket",
    }
    assert analysis.to_dict() == {
        "intent": "Problem",
        "assessment": None,
        "solution_steps": [],
        "routing": {"route": "weiterleiten Policen", "rationale": "Police context"},
        "identifiers": [identifier.to_dict()],
        "command_risks": [risk.to_dict()],
        "uncertainties": ["Niedrige Retrieval-Confidence."],
        "mode": "deterministic",
    }


def test_index_result_serializes_storage_dir_as_string() -> None:
    result = IndexResult(
        status="success",
        indexed_documents=2,
        skipped_documents=1,
        storage_dir=Path("data/storage"),
        message="Indexed 2 Markdown documents.",
    )

    assert result.to_dict() == {
        "status": "success",
        "indexed_documents": 2,
        "skipped_documents": 1,
        "storage_dir": "data/storage",
        "message": "Indexed 2 Markdown documents.",
    }


def test_update_result_serializes_manifest_diagnostics() -> None:
    warning = MetadataWarning(path="runbook.md", field="status", message="Missing status.")
    duplicate = DuplicateGroup(
        group_id="exact:abc123",
        kind="exact",
        canonical_path="runbook.md",
        paths=["runbook.md", "copy.md"],
        score=1.0,
    )
    entry = ManifestEntry(
        path="runbook.md",
        content_hash="content-hash",
        body_hash="body-hash",
        metadata={"status": "active"},
        indexed_at="2026-05-01T00:00:00Z",
        warnings=[warning],
        body_excerpt="Restart the service.",
        duplicate_group_ids=["exact:abc123"],
    )
    diff = ManifestDiff(
        new_paths=["new.md"],
        changed_paths=["changed.md"],
        unchanged_paths=["same.md"],
        deleted_paths=["deleted.md"],
        skipped_paths=["empty.md"],
    )
    result = UpdateResult(
        status="updated",
        indexed_documents=2,
        skipped_documents=1,
        storage_dir=Path("data/storage"),
        manifest_path=Path("data/storage/ood-manifest.json"),
        message="Updated 2 Markdown document(s).",
        diff=diff,
        metadata_warnings=[warning],
        duplicate_groups=[duplicate],
        schema_version=1,
    )

    assert warning.to_dict() == {"path": "runbook.md", "field": "status", "message": "Missing status."}
    assert duplicate.to_dict() == {
        "group_id": "exact:abc123",
        "kind": "exact",
        "canonical_path": "runbook.md",
        "paths": ["runbook.md", "copy.md"],
        "score": 1.0,
    }
    assert entry.to_dict() == {
        "path": "runbook.md",
        "content_hash": "content-hash",
        "body_hash": "body-hash",
        "metadata": {"status": "active"},
        "indexed_at": "2026-05-01T00:00:00Z",
        "warnings": [{"path": "runbook.md", "field": "status", "message": "Missing status."}],
        "body_excerpt": "Restart the service.",
        "duplicate_group_ids": ["exact:abc123"],
    }
    assert result.to_dict() == {
        "status": "updated",
        "indexed_documents": 2,
        "skipped_documents": 1,
        "storage_dir": "data/storage",
        "manifest_path": "data/storage/ood-manifest.json",
        "message": "Updated 2 Markdown document(s).",
        "diff": {
            "new_paths": ["new.md"],
            "changed_paths": ["changed.md"],
            "unchanged_paths": ["same.md"],
            "deleted_paths": ["deleted.md"],
            "skipped_paths": ["empty.md"],
        },
        "metadata_warnings": [{"path": "runbook.md", "field": "status", "message": "Missing status."}],
        "duplicate_groups": [duplicate.to_dict()],
        "schema_version": 1,
    }


def test_index_result_includes_optional_manifest_diagnostics_when_present() -> None:
    warning = MetadataWarning(path="runbook.md", field="quelle", message="Missing quelle.")
    duplicate = DuplicateGroup("near:def456", "near", "runbook.md", ["runbook.md", "similar.md"], 0.91)
    result = IndexResult(
        status="indexed",
        indexed_documents=2,
        skipped_documents=0,
        storage_dir=Path("data/storage"),
        message="Indexed 2 Markdown document(s).",
        metadata_warnings=[warning],
        duplicate_groups=[duplicate],
        manifest_path=Path("data/storage/ood-manifest.json"),
    )

    assert result.to_dict()["metadata_warnings"] == [warning.to_dict()]
    assert result.to_dict()["duplicate_groups"] == [duplicate.to_dict()]
    assert result.to_dict()["manifest_path"] == "data/storage/ood-manifest.json"
