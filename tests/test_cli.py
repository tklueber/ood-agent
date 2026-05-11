from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from ood.cli import app
from ood.models import (
    CommandRisk,
    ConfidenceScore,
    IndexResult,
    ManifestDiff,
    QueryResult,
    RetrievalDiagnostics,
    RoutingDecision,
    SourceHit,
    SourceScoreBreakdown,
    TicketAnalysis,
    TicketIdentifier,
    UpdateResult,
)


runner = CliRunner()


def _ticket_analysis() -> TicketAnalysis:
    return TicketAnalysis(
        intent="Problem",
        assessment=None,
        solution_steps=[],
        routing=RoutingDecision(route="weiterleiten Policen", rationale="Police context"),
        identifiers=[TicketIdentifier(kind="police", value="P-12345", confidence=0.9, evidence="Police P-12345")],
        command_risks=[CommandRisk(command="rm -rf /tmp/cache", risk="rot", rationale="Destructive delete", origin="ticket")],
        uncertainties=["Niedrige Retrieval-Confidence."],
        mode="deterministic",
    )


def test_help_lists_flat_commands() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "index" in result.output
    assert "update" in result.output
    assert "query" in result.output
    assert "status" in result.output
    assert "reindex" in result.output
    assert "mock-init" in result.output
    assert "mock-validate" in result.output


def test_query_requires_ticket_text() -> None:
    missing_query = runner.invoke(app, ["query"])

    assert missing_query.exit_code != 0


def test_index_json_reports_document_counts(tmp_path: Path, monkeypatch) -> None:
    knowledge_dir = tmp_path / "knowledge"
    storage_dir = tmp_path / "storage"
    knowledge_dir.mkdir()
    (knowledge_dir / "runbook.md").write_text("# Restart\nUse the restart workflow.", encoding="utf-8")

    def fake_index(self):
        return IndexResult(
            status="indexed",
            indexed_documents=1,
            skipped_documents=0,
            storage_dir=self.settings.storage_dir,
            message="Indexed 1 Markdown document(s).",
        )

    monkeypatch.setattr("ood.cli.RagEngine.index_markdown", fake_index)

    result = runner.invoke(
        app,
        [
            "index",
            "--json",
            "--knowledge-dir",
            str(knowledge_dir),
            "--storage-dir",
            str(storage_dir),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["command"] == "index"
    assert payload["status"] == "indexed"
    assert payload["indexed_documents"] == 1
    assert payload["skipped_documents"] == 0
    assert payload["storage_dir"] == str(storage_dir)
    assert payload["message"] == "Indexed 1 Markdown document(s)."


def test_reindex_json_reports_rebuild_command(tmp_path: Path, monkeypatch) -> None:
    knowledge_dir = tmp_path / "knowledge"
    storage_dir = tmp_path / "storage"
    knowledge_dir.mkdir()

    def fake_reindex(self):
        return IndexResult(
            status="no_documents",
            indexed_documents=0,
            skipped_documents=0,
            storage_dir=self.settings.storage_dir,
            message="No Markdown documents found to index.",
        )

    monkeypatch.setattr("ood.cli.RagEngine.reindex_markdown", fake_reindex)

    result = runner.invoke(
        app,
        [
            "reindex",
            "--json",
            "--knowledge-dir",
            str(knowledge_dir),
            "--storage-dir",
            str(storage_dir),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["command"] == "reindex"
    assert payload["status"] == "no_documents"
    assert payload["indexed_documents"] == 0
    assert payload["storage_dir"] == str(storage_dir)


def test_empty_knowledge_dir_index_is_successful_noop(tmp_path: Path) -> None:
    knowledge_dir = tmp_path / "missing-knowledge"
    storage_dir = tmp_path / "storage"

    result = runner.invoke(
        app,
        [
            "index",
            "--json",
            "--knowledge-dir",
            str(knowledge_dir),
            "--storage-dir",
            str(storage_dir),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["command"] == "index"
    assert payload["status"] == "no_documents"
    assert payload["indexed_documents"] == 0
    assert payload["skipped_documents"] == 0


def test_query_json_output_matches_phase_2_contract(monkeypatch) -> None:
    def fake_query(self, ticket_text: str):
        return QueryResult(
            query=ticket_text,
            answer=None,
            confidence=ConfidenceScore(score=0.73, rationale="Retrieval-only confidence."),
            sources=[SourceHit(path="tickets/error.md", score=0.91, excerpt="Restart the worker service.")],
            llm_used=False,
            status="success",
            analysis=_ticket_analysis(),
        )

    monkeypatch.setattr("ood.cli.RagEngine.query", fake_query)

    result = runner.invoke(app, ["query", "worker error", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload == {
        "query": "worker error",
        "answer": None,
        "confidence": {"score": 0.73, "rationale": "Retrieval-only confidence."},
        "sources": [
            {"path": "tickets/error.md", "score": 0.91, "excerpt": "Restart the worker service."}
        ],
        "llm_used": False,
        "status": "success",
        "analysis": _ticket_analysis().to_dict(),
        "retrieval_diagnostics": {
            "backend": "unknown",
            "strategy": "unknown",
            "score_components": [],
            "graph_retrieval": {},
            "notes": [],
        },
    }


def test_query_human_output_includes_confidence_and_sources(monkeypatch) -> None:
    def fake_query(self, ticket_text: str):
        return QueryResult(
            query=ticket_text,
            answer=None,
            confidence=ConfidenceScore(score=0.64, rationale="Limited because no LLM credentials are configured."),
            sources=[
                SourceHit(path="runbooks/restart.md", score=0.88, excerpt="Restart via the operations console."),
                SourceHit(path="tickets/prior.md", score=0.71, excerpt="Prior incident used the same fix."),
            ],
            llm_used=False,
            status="success",
            analysis=_ticket_analysis(),
        )

    monkeypatch.setattr("ood.cli.RagEngine.query", fake_query)

    result = runner.invoke(app, ["query", "restart ticket"])

    assert result.exit_code == 0
    assert "Antwort:" in result.output
    assert "Keine generierte Antwort verfügbar; Ausgabe basiert auf Retrieval und deterministischer Analyse." in result.output
    assert "Einschätzung:" in result.output
    assert "Retrieval-only mode; Bewertung basiert auf deterministischer Analyse." in result.output
    assert "Confidence: 0.64" in result.output
    assert "Confidence rationale: Limited because no LLM credentials are configured." in result.output
    assert "Quellen:" in result.output
    assert "1. runbooks/restart.md (score=0.88) — Restart via the operations console." in result.output
    assert "2. tickets/prior.md (score=0.71) — Prior incident used the same fix." in result.output


def test_query_human_output_includes_ticket_analysis_sections(monkeypatch) -> None:
    analysis = TicketAnalysis(
        intent="Problem",
        assessment="Worker login fails for Police P-12345.",
        solution_steps=["Check source evidence.", "Restart worker queue."],
        routing=RoutingDecision(route="weiterleiten Policen", rationale="Police context"),
        identifiers=[TicketIdentifier(kind="police", value="P-12345", confidence=0.9, evidence="Police P-12345")],
        command_risks=[CommandRisk(command="rm -rf /tmp/cache", risk="rot", rationale="Destructive delete", origin="ticket")],
        uncertainties=["Niedrige Retrieval-Confidence."],
        mode="llm_grounded",
    )

    def fake_query(self, ticket_text: str):
        return QueryResult(
            query=ticket_text,
            answer="Worker login fails for Police P-12345.",
            confidence=ConfidenceScore(score=0.64, rationale="Limited because no LLM credentials are configured."),
            sources=[SourceHit(path="runbooks/restart.md", score=0.88, excerpt="Restart via the operations console.")],
            llm_used=True,
            status="success",
            analysis=analysis,
        )

    monkeypatch.setattr("ood.cli.RagEngine.query", fake_query)

    result = runner.invoke(app, ["query", "Police P-12345 Fehler", "--verbose"])

    assert result.exit_code == 0
    assert "Einschätzung:" in result.output
    assert "Worker login fails for Police P-12345." in result.output
    assert "Lösungsweg:" in result.output
    assert "1. Check source evidence." in result.output
    assert "2. Restart worker queue." in result.output
    assert "Routing: weiterleiten Policen — Police context" in result.output
    assert "Quellen:" in result.output
    assert "Unsicherheiten:" in result.output
    assert "Erkannte IDs:" in result.output
    assert "police: P-12345 (confidence=0.9) — Police P-12345" in result.output
    assert "Command Risks:" in result.output
    assert "rot | rm -rf /tmp/cache | ticket | Destructive delete" in result.output
    assert "cloud_llm_allowed=False" in result.output
    assert "analysis_mode=llm_grounded" in result.output
    assert "retrieval_backend=unknown" in result.output
    assert "graph_status=unknown" in result.output


def test_query_verbose_output_renders_retrieval_and_graph_diagnostics(monkeypatch) -> None:
    def fake_query(self, ticket_text: str):
        return QueryResult(
            query=ticket_text,
            answer="Gefundene Hinweise: [1] Restart Phoenix worker.",
            confidence=ConfidenceScore(score=0.81, rationale="Hybrid confidence."),
            sources=[SourceHit(path="runbooks/phoenix.md", score=0.92, excerpt="Restart Phoenix worker.")],
            llm_used=False,
            status="success",
            analysis=TicketAnalysis(
                intent="Problem",
                assessment="Gefundene Hinweise: [1] Restart Phoenix worker.",
                solution_steps=["[1] Restart Phoenix worker."],
                routing=RoutingDecision(route="selbst lösen", rationale="Actionable source"),
                identifiers=[],
                command_risks=[],
                uncertainties=[],
                mode="local_extractive",
            ),
            retrieval_diagnostics=RetrievalDiagnostics(
                backend="local_vector_index",
                strategy="hybrid_semantic_lexical",
                score_components=[
                    SourceScoreBreakdown(
                        path="runbooks/phoenix.md",
                        semantic_score=0.72,
                        lexical_score=1.0,
                        combined_score=0.92,
                        lexical_matches=["phoenix"],
                        weights={"semantic": 0.65, "lexical": 0.35},
                    )
                ],
                graph_retrieval={"status": "deferred", "replacement": "hybrid semantic+lexical retrieval"},
                notes=[],
            ),
        )

    monkeypatch.setattr("ood.cli.RagEngine.query", fake_query)

    result = runner.invoke(app, ["query", "Phoenix Fehler", "--verbose"])

    assert result.exit_code == 0
    assert "analysis_mode=local_extractive" in result.output
    assert "retrieval_backend=local_vector_index" in result.output
    assert "retrieval_strategy=hybrid_semantic_lexical" in result.output
    assert "graph_status=deferred" in result.output
    assert "graph_replacement=hybrid semantic+lexical retrieval" in result.output


def test_query_verbose_output_includes_graph_metadata_components(monkeypatch) -> None:
    def fake_query(self, ticket_text: str):
        return QueryResult(
            query=ticket_text,
            answer="Gefundene Hinweise: [1] TraceId in Kafka finden.",
            confidence=ConfidenceScore(score=0.87, rationale="Hybrid graph confidence."),
            sources=[SourceHit(path="how-to-find-traceid-in-kafka-message.md", score=0.91, excerpt="TraceId in Kafka")],
            llm_used=False,
            status="success",
            analysis=_ticket_analysis(),
            retrieval_diagnostics=RetrievalDiagnostics(
                backend="local_vector_graph_index",
                strategy="hybrid_semantic_lexical_metadata_graph",
                score_components=[
                    SourceScoreBreakdown(
                        path="how-to-find-traceid-in-kafka-message.md",
                        semantic_score=0.12,
                        lexical_score=0.25,
                        combined_score=0.91,
                        lexical_matches=["akhq"],
                        weights={"semantic": 0.2, "metadata": 0.4, "graph": 0.25},
                        metadata_score=1.0,
                        graph_score=0.56,
                        final_score=0.91,
                        metadata_matches=["keyword:TraceId"],
                        graph_matches=["incoming_link:uno-fehler-offerte-verarbeitung.md"],
                    )
                ],
                graph_retrieval={
                    "status": "active",
                    "artifact_path": "data/ood-kb-storage/ood-local-graph-index.json",
                    "document_count": 438,
                    "edge_count": 120,
                },
                notes=["Local retrieval fuses semantic vectors, lexical exact tokens, metadata fields, and Wikilink graph signals."],
            ),
        )

    monkeypatch.setattr("ood.cli.RagEngine.query", fake_query)

    result = runner.invoke(app, ["query", "TraceId Kafka", "--verbose"])

    assert result.exit_code == 0
    assert "retrieval_backend=local_vector_graph_index" in result.output
    assert "retrieval_strategy=hybrid_semantic_lexical_metadata_graph" in result.output
    assert "graph_status=active" in result.output
    assert "graph_documents=438" in result.output
    assert "graph_edges=120" in result.output
    assert "how-to-find-traceid-in-kafka-message.md semantic=0.12 lexical=0.25 metadata=1.0 graph=0.56 final=0.91" in result.output


def test_status_json_reports_paths_and_counts(tmp_path: Path) -> None:
    knowledge_dir = tmp_path / "knowledge"
    storage_dir = tmp_path / "storage"
    knowledge_dir.mkdir()
    storage_dir.mkdir()
    (knowledge_dir / "runbook.md").write_text("# Runbook", encoding="utf-8")
    (storage_dir / "ood-manifest.json").write_text(
        json.dumps({"schema_version": 1, "entries": [{"path": "runbook.md"}]}),
        encoding="utf-8",
    )
    (storage_dir / "ood-local-vector-index.json").write_text(
        json.dumps({"documents": [{"path": "runbook.md"}, {"path": "ticket.md"}]}),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["status", "--json", "--knowledge-dir", str(knowledge_dir), "--storage-dir", str(storage_dir)],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["command"] == "status"
    assert payload["status"] == "ready"
    assert payload["knowledge_dir"] == str(knowledge_dir)
    assert payload["storage_dir"] == str(storage_dir)
    assert payload["manifest_path"] == str(storage_dir / "ood-manifest.json")
    assert payload["vector_index_path"] == str(storage_dir / "ood-local-vector-index.json")
    assert payload["knowledge_documents"] == 1
    assert payload["indexed_documents"] == 1
    assert payload["chunks"] == 2
    assert payload["storage_files"] == 2


def test_status_human_output_summarizes_index_state(tmp_path: Path) -> None:
    knowledge_dir = tmp_path / "knowledge"
    storage_dir = tmp_path / "storage"
    knowledge_dir.mkdir()
    (knowledge_dir / "runbook.md").write_text("# Runbook", encoding="utf-8")

    result = runner.invoke(app, ["status", "--knowledge-dir", str(knowledge_dir), "--storage-dir", str(storage_dir)])

    assert result.exit_code == 0
    assert "Markdown documents exist, but no index artifacts were found. Run `ood index`." in result.output
    assert "Status: not_indexed" in result.output
    assert "Knowledge dir:" in result.output
    assert "Documents: knowledge=1 indexed=0" in result.output
    assert "Chunks: 0" in result.output


def test_query_json_output_matches_phase_4_contract(monkeypatch) -> None:
    def fake_query(self, ticket_text: str):
        return QueryResult(
            query=ticket_text,
            answer=None,
            confidence=ConfidenceScore(score=0.73, rationale="Retrieval-only confidence."),
            sources=[SourceHit(path="tickets/error.md", score=0.91, excerpt="Restart the worker service.")],
            llm_used=False,
            status="success",
            analysis=_ticket_analysis(),
        )

    monkeypatch.setattr("ood.cli.RagEngine.query", fake_query)

    result = runner.invoke(app, ["query", "Police P-12345 Fehler", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert "cloud_llm_allowed" not in payload
    assert payload["query"] == "Police P-12345 Fehler"
    assert payload["sources"][0]["path"] == "tickets/error.md"
    assert payload["analysis"]["routing"]["route"] == "weiterleiten Policen"
    assert payload["analysis"]["identifiers"][0]["value"] == "P-12345"
    assert payload["analysis"]["command_risks"][0]["risk"] == "rot"


def test_query_before_index_exits_nonzero_with_instruction(tmp_path: Path) -> None:
    storage_dir = tmp_path / "storage"

    result = runner.invoke(app, ["query", "test", "--storage-dir", str(storage_dir)])

    assert result.exit_code == 1
    assert "No index found. Run `ood index` first." in result.output


def test_update_json_reports_incremental_diagnostics(tmp_path: Path, monkeypatch) -> None:
    storage_dir = tmp_path / "storage"

    def fake_update(self):
        return UpdateResult(
            status="updated",
            indexed_documents=1,
            skipped_documents=0,
            storage_dir=self.settings.storage_dir,
            manifest_path=self.settings.storage_dir / "ood-manifest.json",
            message="Updated 1 Markdown document(s).",
            diff=ManifestDiff(["new.md"], [], ["same.md"], ["deleted.md"], []),
            metadata_warnings=[],
            duplicate_groups=[],
            schema_version=1,
        )

    monkeypatch.setattr("ood.cli.RagEngine.update_markdown", fake_update)

    result = runner.invoke(app, ["update", "--json", "--storage-dir", str(storage_dir)])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["command"] == "update"
    assert payload["status"] == "updated"
    assert payload["manifest_path"] == str(storage_dir / "ood-manifest.json")
    assert payload["diff"]["new_paths"] == ["new.md"]
    assert payload["diff"]["deleted_paths"] == ["deleted.md"]
    assert payload["metadata_warnings"] == []
    assert payload["duplicate_groups"] == []


def test_update_human_verbose_and_quiet_modes(tmp_path: Path, monkeypatch) -> None:
    storage_dir = tmp_path / "storage"

    def fake_update(self):
        return UpdateResult(
            status="no_changes",
            indexed_documents=0,
            skipped_documents=1,
            storage_dir=self.settings.storage_dir,
            manifest_path=self.settings.storage_dir / "ood-manifest.json",
            message="No knowledge changes detected.",
            diff=ManifestDiff([], [], ["same.md"], [], ["empty.md"]),
            metadata_warnings=[],
            duplicate_groups=[],
            schema_version=1,
        )

    monkeypatch.setattr("ood.cli.RagEngine.update_markdown", fake_update)

    verbose = runner.invoke(app, ["update", "--verbose", "--storage-dir", str(storage_dir)])
    quiet = runner.invoke(app, ["update", "--quiet", "--storage-dir", str(storage_dir)])

    assert verbose.exit_code == 0
    assert "No knowledge changes detected." in verbose.output
    assert "Diagnostics:" in verbose.output
    assert "storage_dir=" in verbose.output
    assert "manifest_path=" in verbose.output
    assert "indexed_documents=0" in verbose.output
    assert "skipped_documents=1" in verbose.output
    assert "new=0" in verbose.output
    assert "changed=0" in verbose.output
    assert "unchanged=1" in verbose.output
    assert "deleted=0" in verbose.output
    assert "warnings=0" in verbose.output
    assert "duplicate_groups=0" in verbose.output
    assert quiet.exit_code == 0
    assert quiet.output == ""


def test_path_overrides_are_passed_to_settings_loader(tmp_path: Path) -> None:
    knowledge_dir = tmp_path / "kb"
    data_dir = tmp_path / "idx"
    storage_dir = tmp_path / "store"

    result = runner.invoke(
        app,
        [
            "index",
            "--json",
            "--knowledge-dir",
            str(knowledge_dir),
            "--data-dir",
            str(data_dir),
            "--storage-dir",
            str(storage_dir),
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["command"] == "index"
    assert payload["status"] == "no_documents"
    assert payload["storage_dir"] == str(storage_dir)


def test_mock_init_json_generates_corpus(tmp_path: Path) -> None:
    target_dir = tmp_path / "knowledge" / "mock" / "v1"

    result = runner.invoke(app, ["mock-init", "--target-dir", str(target_dir), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["command"] == "mock-init"
    assert payload["dataset"] == "mock-v1"
    assert payload["document_count"] >= 12
    assert set(payload["source_types"]) == {"ticket", "wiki", "jira_bug", "servicenow_case", "runbook", "note"}
    assert all(Path(path).exists() for path in payload["generated_paths"])


def test_mock_validate_json_reports_findings_and_coverage(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "knowledge" / "mock" / "v1"
    init_result = runner.invoke(app, ["mock-init", "--target-dir", str(corpus_dir), "--quiet"])
    assert init_result.exit_code == 0

    result = runner.invoke(app, ["mock-validate", "--corpus-dir", str(corpus_dir), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["command"] == "mock-validate"
    assert payload["document_count"] >= 12
    assert payload["is_safe"] is True
    assert payload["findings"] == []
    assert set(payload["coverage"]["source_types"]) == {"ticket", "wiki", "jira_bug", "servicenow_case", "runbook", "note"}


def test_mock_validate_human_output_summarizes_safety_and_coverage(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "knowledge" / "mock" / "v1"
    runner.invoke(app, ["mock-init", "--target-dir", str(corpus_dir), "--quiet"])

    result = runner.invoke(app, ["mock-validate", "--corpus-dir", str(corpus_dir)])
    quiet = runner.invoke(app, ["mock-validate", "--corpus-dir", str(corpus_dir), "--quiet"])

    assert result.exit_code == 0
    assert "Safety: safe" in result.output
    assert "Findings: 0" in result.output
    assert "Coverage:" in result.output
    assert "source_types" in result.output
    assert "routing_targets" in result.output
    assert quiet.exit_code == 0
    assert quiet.output == ""


def test_mock_corpus_indexes_and_reindexes_through_existing_cli_commands(tmp_path: Path, monkeypatch) -> None:
    corpus_dir = tmp_path / "knowledge" / "mock" / "v1"
    storage_dir = tmp_path / "data" / "mock-storage"
    init_result = runner.invoke(app, ["mock-init", "--target-dir", str(corpus_dir), "--quiet"])
    assert init_result.exit_code == 0
    monkeypatch.setattr("ood.rag.LightRAG", None)
    monkeypatch.setattr("ood.rag.RagEngine._encode_local_embeddings", lambda self, texts: [[1.0, 0.0] for _ in texts])

    index_result = runner.invoke(
        app,
        [
            "index",
            "--json",
            "--knowledge-dir",
            str(corpus_dir),
            "--storage-dir",
            str(storage_dir),
        ],
    )
    reindex_result = runner.invoke(
        app,
        [
            "reindex",
            "--json",
            "--knowledge-dir",
            str(corpus_dir),
            "--storage-dir",
            str(storage_dir),
        ],
    )

    assert index_result.exit_code == 0
    assert reindex_result.exit_code == 0
    for command, result in (("index", index_result), ("reindex", reindex_result)):
        payload = json.loads(result.output)
        assert payload["command"] == command
        assert payload["status"] == "indexed"
        assert payload["indexed_documents"] >= 12
        assert payload["skipped_documents"] == 0
        assert payload["manifest_path"] == str(storage_dir / "ood-manifest.json")
        assert "metadata_warnings" not in payload


def test_mock_corpus_update_reports_added_changed_unchanged_and_deleted_paths(tmp_path: Path, monkeypatch) -> None:
    corpus_dir = tmp_path / "knowledge" / "mock" / "v1"
    storage_dir = tmp_path / "data" / "mock-storage"
    init_result = runner.invoke(app, ["mock-init", "--target-dir", str(corpus_dir), "--quiet"])
    assert init_result.exit_code == 0
    monkeypatch.setattr("ood.rag.LightRAG", None)
    monkeypatch.setattr("ood.rag.RagEngine._encode_local_embeddings", lambda self, texts: [[1.0, 0.0] for _ in texts])
    index_result = runner.invoke(
        app,
        ["index", "--json", "--knowledge-dir", str(corpus_dir), "--storage-dir", str(storage_dir)],
    )
    assert index_result.exit_code == 0

    generated_paths = sorted(corpus_dir.rglob("*.md"), key=lambda path: path.as_posix())
    changed_path = generated_paths[0]
    deleted_path = generated_paths[1]
    source_for_new = generated_paths[2]
    unchanged_path = generated_paths[3]
    changed_path.write_text(
        changed_path.read_text(encoding="utf-8") + "\nSynthetische Zusatznotiz für Update-Diagnostik.\n",
        encoding="utf-8",
    )
    new_path = source_for_new.parent / "mock-added-update.md"
    new_content = source_for_new.read_text(encoding="utf-8")
    new_content = new_content.replace("synthetic_id: MOCK-", "synthetic_id: MOCK-ADDED-", 1)
    new_content = new_content.replace("title: ", "title: Added Update Copy - ", 1)
    new_content = new_content.replace("Synthetische Referenz: MOCK-", "Synthetische Referenz: MOCK-ADDED-", 1)
    new_path.write_text(new_content, encoding="utf-8")
    deleted_path.unlink()

    update_result = runner.invoke(
        app,
        ["update", "--json", "--knowledge-dir", str(corpus_dir), "--storage-dir", str(storage_dir)],
    )

    assert update_result.exit_code == 0
    payload = json.loads(update_result.output)
    diff = payload["diff"]
    assert payload["command"] == "update"
    assert payload["status"] == "updated"
    assert payload["indexed_documents"] == 2
    assert diff["new_paths"] == [new_path.relative_to(corpus_dir).as_posix()]
    assert diff["changed_paths"] == [changed_path.relative_to(corpus_dir).as_posix()]
    assert diff["deleted_paths"] == [deleted_path.relative_to(corpus_dir).as_posix()]
    assert unchanged_path.relative_to(corpus_dir).as_posix() in diff["unchanged_paths"]
    assert payload["metadata_warnings"] == []
    assert isinstance(payload["duplicate_groups"], list)


def test_quality_audit_json_reports_retrieval_readiness(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "articles"
    corpus_dir.mkdir()
    (corpus_dir / "traceid.md").write_text(
        "---\ntitle: TraceId Kafka\ntype: runbook\nservice: Kafka\nkeywords: TraceId\n---\nTraceId Kafka.",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["quality-audit", "--corpus-dir", str(corpus_dir), "--expected-documents", "438", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["command"] == "quality-audit"
    assert payload["document_count"] == 1
    assert payload["expected_documents"] == 438
    assert payload["expected_document_mismatch"] is True
    assert payload["recommendations"]


def test_quality_audit_writes_report_path(tmp_path: Path) -> None:
    corpus_dir = tmp_path / "articles"
    report_path = tmp_path / "reports" / "quality.json"
    corpus_dir.mkdir()
    (corpus_dir / "note.md").write_text("# Note\nNo metadata.", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "quality-audit",
            "--corpus-dir",
            str(corpus_dir),
            "--expected-documents",
            "1",
            "--report-path",
            str(report_path),
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert report_path.exists()
    written = json.loads(report_path.read_text(encoding="utf-8"))
    assert written == json.loads(result.output)
