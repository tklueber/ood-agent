from __future__ import annotations

import json
from pathlib import Path

from pydantic import SecretStr

from ood.config import Settings
from ood.models import IndexMissingError, IndexResult
from ood.rag import LOCAL_GRAPH_INDEX_FILENAME, LOCAL_VECTOR_INDEX_FILENAME, RagEngine


class FakeLightRAG:
    instances: list["FakeLightRAG"] = []
    query_data_payload: dict[str, object] = {"data": {"chunks": []}}
    query_answer: str = "Generated fix."

    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs
        self.inserted_documents: list[str] | None = None
        self.inserted_paths: list[str] | None = None
        FakeLightRAG.instances.append(self)

    async def ainsert(self, documents: list[str], *, file_paths: list[str]) -> None:
        self.inserted_documents = documents
        self.inserted_paths = file_paths

    async def aquery_data(self, query_text: str, query_param: object) -> dict[str, object]:
        self.query_text = query_text
        self.query_param = query_param
        return self.query_data_payload

    async def aquery(self, query_text: str, *, param: object) -> str:
        self.answer_query_text = query_text
        self.answer_param = param
        return self.query_answer


def _settings(
    tmp_path: Path,
    *,
    llm_api_key: SecretStr | None = None,
    allow_cloud_llm: bool = False,
) -> Settings:
    return Settings(
        knowledge_dir=tmp_path / "knowledge",
        data_dir=tmp_path / "data",
        storage_dir=tmp_path / "data" / "storage",
        llm_provider="openai" if llm_api_key else None,
        llm_api_key=llm_api_key,
        allow_cloud_llm=allow_cloud_llm,
    )


def _patch_lightrag(monkeypatch) -> None:
    FakeLightRAG.instances.clear()
    FakeLightRAG.query_data_payload = {"data": {"chunks": []}}
    FakeLightRAG.query_answer = "Generated fix."
    monkeypatch.setattr("ood.rag.LightRAG", FakeLightRAG)
    monkeypatch.setattr(RagEngine, "_build_embedding_func", lambda self: object())


def test_index_markdown_discovers_recursive_plain_markdown(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    (settings.knowledge_dir / "apps").mkdir(parents=True)
    (settings.knowledge_dir / "runbook.md").write_text("# Root\nFix root issue.", encoding="utf-8")
    (settings.knowledge_dir / "apps" / "runbook.md").write_text(
        "Plain Markdown without frontmatter.", encoding="utf-8"
    )
    (settings.knowledge_dir / "apps" / "empty.md").write_text("  \n\t", encoding="utf-8")
    (settings.knowledge_dir / "ignore.txt").write_text("not markdown", encoding="utf-8")
    _patch_lightrag(monkeypatch)

    result = RagEngine(settings).index_markdown()

    assert isinstance(result, IndexResult)
    assert result.status == "indexed"
    assert result.indexed_documents == 2
    assert result.skipped_documents == 1
    assert result.storage_dir == settings.storage_dir
    assert settings.storage_dir.exists()
    assert len(FakeLightRAG.instances) == 1
    rag = FakeLightRAG.instances[0]
    assert rag.kwargs["working_dir"] == str(settings.storage_dir)
    assert rag.inserted_paths == ["apps/runbook.md", "runbook.md"]
    assert rag.inserted_documents == ["Plain Markdown without frontmatter.", "# Root\nFix root issue."]


def test_frontmatter_is_stripped_before_indexing(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.knowledge_dir.mkdir(parents=True)
    (settings.knowledge_dir / "runbook.md").write_text(
        "---\n"
        "Quelle: Wiki\n"
        "Datum: '2026-05-01'\n"
        "Status: active\n"
        "System: ERP\n"
        "Komponente: Worker\n"
        "Title: Restart worker\n"
        "Type: runbook\n"
        "---\n"
        "# Restart worker\nUse the operations console.",
        encoding="utf-8",
    )
    _patch_lightrag(monkeypatch)

    result = RagEngine(settings).index_markdown()

    assert result.status == "indexed"
    rag = FakeLightRAG.instances[0]
    assert rag.inserted_documents == ["# Restart worker\nUse the operations console."]
    parsed = RagEngine(settings)._parse_markdown_document(settings.knowledge_dir / "runbook.md")
    assert parsed.metadata == {
        "quelle": "Wiki",
        "datum": "2026-05-01",
        "status": "active",
        "system": "ERP",
        "komponente": "Worker",
        "title": "Restart worker",
        "type": "runbook",
    }
    assert len(parsed.content_hash) == 64
    assert len(parsed.body_hash) == 64


def test_metadata_warnings_are_non_blocking(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.knowledge_dir.mkdir(parents=True)
    (settings.knowledge_dir / "plain.md").write_text("Plain body text.", encoding="utf-8")
    (settings.knowledge_dir / "bad-status.md").write_text(
        "---\nquelle: Wiki\ndatum: 2026-05-01\nstatus: stale\nsystem: ERP\nkomponente: UI\ntitle: Bad\ntype: note\n---\nBody",
        encoding="utf-8",
    )
    _patch_lightrag(monkeypatch)

    result = RagEngine(settings).index_markdown()

    assert result.status == "indexed"
    assert result.indexed_documents == 2
    plain = RagEngine(settings)._parse_markdown_document(settings.knowledge_dir / "plain.md")
    bad = RagEngine(settings)._parse_markdown_document(settings.knowledge_dir / "bad-status.md")
    assert {warning.field for warning in plain.warnings} == {
        "quelle",
        "datum",
        "status",
        "system",
        "komponente",
        "title",
        "type",
    }
    assert [warning.field for warning in bad.warnings] == ["status"]
    assert FakeLightRAG.instances[0].inserted_paths == ["bad-status.md", "plain.md"]


def test_index_writes_manifest_with_metadata_and_hashes(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.knowledge_dir.mkdir(parents=True)
    (settings.knowledge_dir / "runbook.md").write_text(
        "---\nquelle: Wiki\ndatum: 2026-05-01\nstatus: active\nsystem: ERP\nkomponente: Worker\ntitle: Restart\ntype: runbook\n---\nRestart the worker.",
        encoding="utf-8",
    )
    _patch_lightrag(monkeypatch)

    result = RagEngine(settings).index_markdown()

    manifest_path = settings.storage_dir / "ood-manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert result.manifest_path == manifest_path
    assert result.metadata_warnings == []
    assert payload["schema_version"] == 1
    assert payload["generated_at"].endswith("Z")
    assert payload["duplicate_groups"] == []
    assert payload["entries"][0]["path"] == "runbook.md"
    assert payload["entries"][0]["metadata"]["quelle"] == "Wiki"
    assert len(payload["entries"][0]["content_hash"]) == 64
    assert len(payload["entries"][0]["body_hash"]) == 64
    assert payload["entries"][0]["body_excerpt"] == "Restart the worker."


def test_fallback_index_uses_frontmatter_stripped_body(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.knowledge_dir.mkdir(parents=True)
    (settings.knowledge_dir / "runbook.md").write_text(
        "---\nquelle: Wiki\ndatum: 2026-05-01\nstatus: active\nsystem: ERP\nkomponente: Worker\ntitle: Restart\ntype: runbook\n---\nBody only.",
        encoding="utf-8",
    )
    monkeypatch.setattr("ood.rag.LightRAG", None)
    monkeypatch.setattr(RagEngine, "_encode_local_embeddings", lambda self, texts: [[0.1, 0.2, 0.3] for _ in texts])

    result = RagEngine(settings).index_markdown()

    fallback = json.loads((settings.storage_dir / LOCAL_VECTOR_INDEX_FILENAME).read_text(encoding="utf-8"))
    assert result.status == "indexed"
    assert fallback["documents"] == [
        {"path": "runbook.md", "content": "Body only.", "excerpt": "Body only.", "vector": [0.1, 0.2, 0.3]}
    ]
    assert "quelle: Wiki" not in fallback["documents"][0]["content"]


def test_index_writes_local_graph_metadata_artifact(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.knowledge_dir.mkdir(parents=True)
    (settings.knowledge_dir / "how-to-find-traceid-in-kafka-message.md").write_text(
        "---\n"
        "title: How to find TraceId in Kafka message\n"
        "type: runbook\n"
        "service: Kafka\n"
        "system: AKHQ\n"
        "component: Ersatzgeschäft\n"
        "keywords:\n"
        "  - TraceId\n"
        "  - Kafka message\n"
        "aliases:\n"
        "  - correlation id\n"
        "tags: [troubleshooting, kafka]\n"
        "related:\n"
        "  - uno-fehler-offerte-verarbeitung\n"
        "---\n"
        "# TraceId in Kafka finden\n"
        "Siehe [[uno-fehler-offerte-verarbeitung]] und [[how-to-splunk]].\n\n"
        "## Commands\n"
        "```bash\n"
        "kubectl logs deploy/akhq | grep TraceId\n"
        "```\n",
        encoding="utf-8",
    )
    (settings.knowledge_dir / "uno-fehler-offerte-verarbeitung.md").write_text(
        "---\ntitle: UNO Fehler Offerte Verarbeitung\ntype: ticket\nservice: UNO\nkeywords: [Ersatzgeschäft]\n---\n"
        "Verlinkt auf [[how-to-find-traceid-in-kafka-message]].",
        encoding="utf-8",
    )
    monkeypatch.setattr("ood.rag.LightRAG", None)
    monkeypatch.setattr(RagEngine, "_encode_local_embeddings", lambda self, texts: [[0.1, 0.2] for _ in texts])

    result = RagEngine(settings).index_markdown()

    graph_path = settings.storage_dir / LOCAL_GRAPH_INDEX_FILENAME
    payload = json.loads(graph_path.read_text(encoding="utf-8"))
    target = next(doc for doc in payload["documents"] if doc["path"] == "how-to-find-traceid-in-kafka-message.md")
    assert result.status == "indexed"
    assert payload["schema_version"] == 1
    assert target["title"] == "How to find TraceId in Kafka message"
    assert target["service"] == "Kafka"
    assert target["system"] == "AKHQ"
    assert target["component"] == "Ersatzgeschäft"
    assert "TraceId" in target["keywords"]
    assert "correlation id" in target["aliases"]
    assert "TraceId in Kafka finden" in target["headings"]
    assert "kubectl logs deploy/akhq | grep TraceId" in target["commands"]
    assert "uno-fehler-offerte-verarbeitung" in target["outgoing_wikilinks"]
    assert target["incoming_link_count"] == 1
    assert "traceid" in target["search_tokens"]
    assert {edge["source"] for edge in payload["edges"]} == {
        "how-to-find-traceid-in-kafka-message.md",
        "uno-fehler-offerte-verarbeitung.md",
    }


def test_update_writes_graph_artifact_even_when_no_documents_changed(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.knowledge_dir.mkdir(parents=True)
    (settings.knowledge_dir / "runbook.md").write_text("# Runbook\nUse [[other]].", encoding="utf-8")
    monkeypatch.setattr("ood.rag.LightRAG", None)
    monkeypatch.setattr(RagEngine, "_encode_local_embeddings", lambda self, texts: [[0.1, 0.2] for _ in texts])
    RagEngine(settings).index_markdown()
    (settings.storage_dir / LOCAL_GRAPH_INDEX_FILENAME).unlink()

    result = RagEngine(settings).update_markdown()

    assert result.status == "no_changes"
    assert (settings.storage_dir / LOCAL_GRAPH_INDEX_FILENAME).exists()


def test_local_graph_metadata_scoring_matches_traceid_frontmatter(tmp_path) -> None:
    settings = _settings(tmp_path)
    settings.storage_dir.mkdir(parents=True)
    graph_index = {
        "schema_version": 1,
        "documents": [
            {
                "path": "how-to-find-traceid-in-kafka-message.md",
                "title": "How to find TraceId in Kafka message",
                "type": "runbook",
                "service": "Kafka",
                "system": "AKHQ",
                "component": "Ersatzgeschäft",
                "keywords": ["TraceId", "Kafka message"],
                "aliases": ["correlation id"],
                "tags": ["kafka"],
                "headings": ["TraceId in Kafka finden"],
                "commands": ["kubectl logs deploy/akhq | grep TraceId"],
                "outgoing_wikilinks": ["how-to-splunk"],
                "incoming_link_count": 1,
                "search_tokens": ["traceid", "kafka", "akhq", "ersatzgeschäft"],
            },
            {
                "path": "how-to-splunk.md",
                "title": "Splunk TraceId Suche",
                "type": "runbook",
                "service": "Splunk",
                "keywords": ["TraceId"],
                "search_tokens": ["splunk", "traceid"],
            },
        ],
        "edges": [
            {
                "source": "how-to-find-traceid-in-kafka-message.md",
                "target": "how-to-splunk.md",
                "label": "wikilink",
            },
            {
                "source": "uno-fehler-offerte-verarbeitung.md",
                "target": "how-to-find-traceid-in-kafka-message.md",
                "label": "wikilink",
            },
        ],
    }
    (settings.storage_dir / LOCAL_GRAPH_INDEX_FILENAME).write_text(json.dumps(graph_index), encoding="utf-8")
    engine = RagEngine(settings)
    graph = engine._read_local_graph_index()
    target = graph["documents_by_path"]["how-to-find-traceid-in-kafka-message.md"]
    query_tokens = engine._tokenize("TraceId Kafka AKHQ Ersatzgeschäft")

    metadata_score, metadata_matches = engine._score_metadata_match(query_tokens, target)
    graph_score, graph_matches = engine._score_graph_match(query_tokens, target, graph)

    assert metadata_score >= 0.8
    assert "keyword:TraceId" in metadata_matches
    assert "service:Kafka" in metadata_matches
    assert "system:AKHQ" in metadata_matches
    assert "component:Ersatzgeschäft" in metadata_matches
    assert graph_score > 0.0
    assert "link:how-to-splunk.md" in graph_matches
    assert "incoming_link:uno-fehler-offerte-verarbeitung.md" in graph_matches


def test_traceid_kafka_query_is_promoted_by_metadata_graph_fusion(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.storage_dir.mkdir(parents=True)
    monkeypatch.setattr("ood.rag.LightRAG", None)
    vector_payload = {
        "documents": [
            {
                "path": "ersatzgeschaeft-body-similar.md",
                "content": "Ersatzgeschäft Verarbeitung Offerte Fehler Retry Worker",
                "excerpt": "Ersatzgeschäft Verarbeitung Offerte Fehler Retry Worker",
                "vector": [1.0, 0.0],
            },
            {
                "path": "how-to-find-traceid-in-kafka-message.md",
                "content": "Kurzer Hinweis zum Lesen einer Nachricht in AKHQ.",
                "excerpt": "Kurzer Hinweis zum Lesen einer Nachricht in AKHQ.",
                "vector": [0.0, 1.0],
            },
        ]
    }
    graph_payload = {
        "schema_version": 1,
        "documents": [
            {
                "path": "ersatzgeschaeft-body-similar.md",
                "title": "Ersatzgeschäft Retry",
                "type": "note",
                "service": "UNO",
                "keywords": ["Ersatzgeschäft"],
                "search_tokens": ["ersatzgeschäft", "retry"],
                "incoming_link_count": 0,
                "outgoing_wikilinks": [],
            },
            {
                "path": "how-to-find-traceid-in-kafka-message.md",
                "title": "How to find TraceId in Kafka message",
                "type": "runbook",
                "service": "Kafka",
                "system": "AKHQ",
                "component": "Ersatzgeschäft",
                "keywords": ["TraceId", "Kafka message"],
                "aliases": ["correlation id"],
                "headings": ["TraceId in Kafka finden"],
                "outgoing_wikilinks": ["how-to-splunk"],
                "incoming_link_count": 1,
                "search_tokens": ["traceid", "kafka", "akhq", "ersatzgeschäft"],
            },
            {
                "path": "how-to-splunk.md",
                "title": "Splunk TraceId Suche",
                "keywords": ["TraceId"],
                "search_tokens": ["splunk", "traceid"],
            },
        ],
        "edges": [
            {"source": "how-to-find-traceid-in-kafka-message.md", "target": "how-to-splunk.md", "label": "wikilink"},
            {"source": "uno-fehler-offerte-verarbeitung.md", "target": "how-to-find-traceid-in-kafka-message.md", "label": "wikilink"},
        ],
    }
    (settings.storage_dir / LOCAL_VECTOR_INDEX_FILENAME).write_text(json.dumps(vector_payload), encoding="utf-8")
    (settings.storage_dir / LOCAL_GRAPH_INDEX_FILENAME).write_text(json.dumps(graph_payload), encoding="utf-8")
    monkeypatch.setattr(RagEngine, "_encode_local_embeddings", lambda self, texts: [[1.0, 0.0]])

    result = RagEngine(settings).query("TraceId Kafka AKHQ Ersatzgeschäft")

    assert result.sources[0].path == "how-to-find-traceid-in-kafka-message.md"
    details = result.sources[0].score_details
    assert details["semantic_score"] < result.sources[1].score_details["semantic_score"]
    assert details["metadata_score"] >= 0.8
    assert details["graph_score"] > 0.0
    assert details["final_score"] == details["combined_score"]
    diagnostics = result.to_dict()["retrieval_diagnostics"]
    assert diagnostics["backend"] == "local_vector_graph_index"
    assert diagnostics["strategy"] == "hybrid_semantic_lexical_metadata_graph"
    assert diagnostics["graph_retrieval"]["status"] == "active"


def test_query_without_llm_uses_hybrid_scoring_to_lift_exact_operational_tokens(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.storage_dir.mkdir(parents=True)
    monkeypatch.setattr("ood.rag.LightRAG", None)
    payload = {
        "documents": [
            {
                "path": "lexical.md",
                "content": "Police P-12345 reports ERR-502 in Phoenix login.",
                "excerpt": "Police P-12345 reports ERR-502 in Phoenix login.",
                "vector": [0.0, 1.0],
            },
            {
                "path": "semantic.md",
                "content": "operations queue remediation",
                "excerpt": "operations queue remediation",
                "vector": [1.0, 0.0],
            },
        ]
    }
    (settings.storage_dir / LOCAL_VECTOR_INDEX_FILENAME).write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(RagEngine, "_encode_local_embeddings", lambda self, texts: [[1.0, 0.0]])

    result = RagEngine(settings).query("Police P-12345 ERR-502 login")

    assert result.status == "success"
    assert [source.path for source in result.sources] == ["lexical.md", "semantic.md"]
    assert 0.0 <= result.sources[0].score <= 1.0
    assert result.sources[0].score > result.sources[1].score
    assert result.sources[0].score_details["semantic_score"] == 0.0
    assert "p-12345" in result.sources[0].score_details["lexical_matches"]
    diagnostics = result.to_dict()["retrieval_diagnostics"]
    assert diagnostics["backend"] == "local_vector_index"
    assert diagnostics["strategy"] == "hybrid_semantic_lexical"
    assert diagnostics["score_components"][0]["path"] == "lexical.md"
    assert diagnostics["score_components"][0]["semantic_score"] == 0.0
    assert diagnostics["score_components"][0]["lexical_score"] > 0.0
    assert diagnostics["score_components"][0]["combined_score"] == result.sources[0].score_details["combined_score"]
    assert diagnostics["graph_retrieval"]["status"] == "deferred"
    assert result.answer is not None
    assert "[1]" in result.answer
    assert result.llm_used is False


def test_query_without_llm_ignores_malformed_vector_index(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.storage_dir.mkdir(parents=True)
    monkeypatch.setattr("ood.rag.LightRAG", None)
    (settings.storage_dir / LOCAL_VECTOR_INDEX_FILENAME).write_text(
        json.dumps({"documents": [{"path": "bad.md", "content": "bad", "vector": "not-a-vector"}]}),
        encoding="utf-8",
    )

    result = RagEngine(settings).query("anything")

    assert result.status == "no_results"
    assert result.sources == []


def test_index_reports_exact_and_near_duplicates_without_skipping(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.knowledge_dir.mkdir(parents=True)
    frontmatter = "---\nquelle: Wiki\ndatum: 2026-05-01\nstatus: active\nsystem: ERP\nkomponente: Worker\ntitle: Dup\ntype: runbook\n---\n"
    (settings.knowledge_dir / "a.md").write_text(frontmatter + "Restart worker queue after timeout.", encoding="utf-8")
    (settings.knowledge_dir / "b.md").write_text(frontmatter + "Restart worker queue after timeout.", encoding="utf-8")
    (settings.knowledge_dir / "near.md").write_text(
        frontmatter + "Restart worker queue after timeout", encoding="utf-8"
    )
    _patch_lightrag(monkeypatch)

    result = RagEngine(settings).index_markdown()

    assert result.indexed_documents == 3
    assert FakeLightRAG.instances[0].inserted_paths == ["a.md", "b.md", "near.md"]
    kinds = {group.kind for group in result.duplicate_groups}
    assert {"exact", "near"} <= kinds
    manifest = json.loads((settings.storage_dir / "ood-manifest.json").read_text(encoding="utf-8"))
    assert manifest["duplicate_groups"] == [group.to_dict() for group in result.duplicate_groups]
    assert all(entry["duplicate_group_ids"] for entry in manifest["entries"])


def test_duplicate_canonical_prefers_active_newest_then_path(tmp_path) -> None:
    settings = _settings(tmp_path)
    settings.knowledge_dir.mkdir(parents=True)
    body = "Same duplicated body."
    (settings.knowledge_dir / "draft-new.md").write_text(
        "---\nquelle: Wiki\ndatum: 2026-06-01\nstatus: draft\nsystem: ERP\nkomponente: UI\ntitle: Draft\ntype: note\n---\n" + body,
        encoding="utf-8",
    )
    (settings.knowledge_dir / "active-old.md").write_text(
        "---\nquelle: Wiki\ndatum: 2026-01-01\nstatus: active\nsystem: ERP\nkomponente: UI\ntitle: Active old\ntype: note\n---\n" + body,
        encoding="utf-8",
    )
    (settings.knowledge_dir / "active-new.md").write_text(
        "---\nquelle: Wiki\ndatum: 2026-05-01\nstatus: active\nsystem: ERP\nkomponente: UI\ntitle: Active new\ntype: note\n---\n" + body,
        encoding="utf-8",
    )

    parsed, _ = RagEngine(settings)._load_parsed_markdown_documents()
    groups = RagEngine(settings)._detect_duplicates(parsed)

    exact = next(group for group in groups if group.kind == "exact")
    assert exact.canonical_path == "active-new.md"


def test_update_bootstraps_manifest_and_indexes_all_when_missing(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.knowledge_dir.mkdir(parents=True)
    (settings.knowledge_dir / "a.md").write_text("# A", encoding="utf-8")
    (settings.knowledge_dir / "b.md").write_text("# B", encoding="utf-8")
    _patch_lightrag(monkeypatch)

    result = RagEngine(settings).update_markdown()

    assert result.status == "updated"
    assert result.indexed_documents == 2
    assert result.diff.new_paths == ["a.md", "b.md"]
    assert result.diff.changed_paths == []
    assert (settings.storage_dir / "ood-manifest.json").exists()
    assert FakeLightRAG.instances[0].inserted_paths == ["a.md", "b.md"]


def test_update_indexes_only_new_and_changed_files(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.knowledge_dir.mkdir(parents=True)
    (settings.knowledge_dir / "same.md").write_text("Same", encoding="utf-8")
    (settings.knowledge_dir / "changed.md").write_text("Old", encoding="utf-8")
    _patch_lightrag(monkeypatch)
    RagEngine(settings).index_markdown()
    FakeLightRAG.instances.clear()
    (settings.knowledge_dir / "changed.md").write_text("New", encoding="utf-8")
    (settings.knowledge_dir / "new.md").write_text("Brand new", encoding="utf-8")

    result = RagEngine(settings).update_markdown()

    assert result.status == "updated"
    assert result.indexed_documents == 2
    assert result.diff.new_paths == ["new.md"]
    assert result.diff.changed_paths == ["changed.md"]
    assert result.diff.unchanged_paths == ["same.md"]
    assert FakeLightRAG.instances[0].inserted_paths == ["changed.md", "new.md"]


def test_update_no_changes_is_successful_noop(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.knowledge_dir.mkdir(parents=True)
    (settings.knowledge_dir / "same.md").write_text("Same", encoding="utf-8")
    _patch_lightrag(monkeypatch)
    RagEngine(settings).index_markdown()
    FakeLightRAG.instances.clear()

    result = RagEngine(settings).update_markdown()

    assert result.status == "no_changes"
    assert result.indexed_documents == 0
    assert result.diff.unchanged_paths == ["same.md"]
    assert FakeLightRAG.instances == []


def test_update_reports_deleted_paths_without_lightrag_delete(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.knowledge_dir.mkdir(parents=True)
    deleted = settings.knowledge_dir / "deleted.md"
    deleted.write_text("Delete me", encoding="utf-8")
    _patch_lightrag(monkeypatch)
    RagEngine(settings).index_markdown()
    FakeLightRAG.instances.clear()
    deleted.unlink()

    result = RagEngine(settings).update_markdown()

    assert result.status == "stale_entries"
    assert result.indexed_documents == 0
    assert result.diff.deleted_paths == ["deleted.md"]
    assert FakeLightRAG.instances == []


def test_update_rejects_incompatible_manifest_schema(tmp_path) -> None:
    settings = _settings(tmp_path)
    settings.knowledge_dir.mkdir(parents=True)
    (settings.knowledge_dir / "a.md").write_text("A", encoding="utf-8")
    settings.storage_dir.mkdir(parents=True)
    (settings.storage_dir / "ood-manifest.json").write_text(
        json.dumps({"schema_version": 999, "entries": []}), encoding="utf-8"
    )

    try:
        RagEngine(settings).update_markdown()
    except ValueError as exc:
        assert str(exc) == "Manifest schema version is incompatible. Run `ood reindex` to rebuild the knowledge manifest."
    else:  # pragma: no cover - assertion helper
        raise AssertionError("expected incompatible manifest schema error")


def test_index_missing_or_empty_knowledge_dir_is_successful_noop(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    _patch_lightrag(monkeypatch)

    missing_result = RagEngine(settings).index_markdown()

    assert missing_result.status == "no_documents"
    assert missing_result.indexed_documents == 0
    assert missing_result.skipped_documents == 0
    assert settings.storage_dir.exists()
    assert FakeLightRAG.instances == []

    settings.knowledge_dir.mkdir(parents=True)
    (settings.knowledge_dir / "empty.md").write_text("\n\n", encoding="utf-8")
    empty_result = RagEngine(settings).index_markdown()

    assert empty_result.status == "no_documents"
    assert empty_result.indexed_documents == 0
    assert empty_result.skipped_documents == 1
    assert FakeLightRAG.instances == []


def test_index_without_llm_credentials_uses_noop_and_no_cloud_calls(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.knowledge_dir.mkdir(parents=True)
    (settings.knowledge_dir / "note.md").write_text("# Local only", encoding="utf-8")
    _patch_lightrag(monkeypatch)
    monkeypatch.setattr(
        "ood.rag.openai_complete_if_cache",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("cloud LLM called")),
    )

    result = RagEngine(settings).index_markdown()

    assert result.status == "indexed"
    llm_func = FakeLightRAG.instances[0].kwargs["llm_model_func"]
    assert llm_func is RagEngine._noop_llm_model_func


def test_index_with_llm_credentials_passes_non_noop_lightrag_llm_func(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path, llm_api_key=SecretStr("test-secret"), allow_cloud_llm=True)
    settings.knowledge_dir.mkdir(parents=True)
    (settings.knowledge_dir / "note.md").write_text("# Cloud enabled", encoding="utf-8")
    _patch_lightrag(monkeypatch)
    calls: list[dict[str, object]] = []

    async def fake_complete(model: str, prompt: str, **kwargs: object) -> str:
        calls.append({"model": model, "prompt": prompt, **kwargs})
        return "ok"

    monkeypatch.setattr("ood.rag.openai_complete_if_cache", fake_complete)

    result = RagEngine(settings).index_markdown()

    assert result.status == "indexed"
    llm_func = FakeLightRAG.instances[0].kwargs["llm_model_func"]
    assert llm_func is not RagEngine._noop_llm_model_func
    assert callable(llm_func)


def test_index_with_llm_credentials_without_approval_uses_noop(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path, llm_api_key=SecretStr("test-secret"))
    settings.knowledge_dir.mkdir(parents=True)
    (settings.knowledge_dir / "note.md").write_text("# Cloud not approved", encoding="utf-8")
    _patch_lightrag(monkeypatch)
    monkeypatch.setattr(
        "ood.rag.openai_complete_if_cache",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("cloud LLM called")),
    )

    result = RagEngine(settings).index_markdown()

    assert result.status == "indexed"
    llm_func = FakeLightRAG.instances[0].kwargs["llm_model_func"]
    assert llm_func is RagEngine._noop_llm_model_func


def test_reindex_clears_only_storage_dir_before_rebuild(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.knowledge_dir.mkdir(parents=True)
    (settings.knowledge_dir / "runbook.md").write_text("# Current", encoding="utf-8")
    settings.storage_dir.mkdir(parents=True)
    (settings.storage_dir / "old-vector.json").write_text("old", encoding="utf-8")
    (settings.storage_dir / "nested").mkdir()
    (settings.storage_dir / "nested" / "old-graph.json").write_text("old", encoding="utf-8")
    sibling_file = settings.data_dir / "outside-storage.txt"
    sibling_file.write_text("keep", encoding="utf-8")
    _patch_lightrag(monkeypatch)

    result = RagEngine(settings).reindex_markdown()

    assert result.status == "indexed"
    assert not (settings.storage_dir / "old-vector.json").exists()
    assert not (settings.storage_dir / "nested").exists()
    assert sibling_file.read_text(encoding="utf-8") == "keep"
    assert (settings.knowledge_dir / "runbook.md").read_text(encoding="utf-8") == "# Current"
    assert FakeLightRAG.instances[0].inserted_paths == ["runbook.md"]


def test_index_does_not_clear_existing_storage(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.knowledge_dir.mkdir(parents=True)
    (settings.knowledge_dir / "runbook.md").write_text("# Current", encoding="utf-8")
    settings.storage_dir.mkdir(parents=True)
    preserved_file = settings.storage_dir / "existing-index.json"
    preserved_file.write_text("keep", encoding="utf-8")
    _patch_lightrag(monkeypatch)

    result = RagEngine(settings).index_markdown()

    assert result.status == "indexed"
    assert preserved_file.read_text(encoding="utf-8") == "keep"
    assert FakeLightRAG.instances[0].inserted_paths == ["runbook.md"]


def test_query_without_llm_returns_ranked_sources_and_null_answer(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.knowledge_dir.mkdir(parents=True)
    absolute_path = settings.knowledge_dir / "tickets" / "incident.md"
    absolute_path.parent.mkdir()
    absolute_path.write_text("# Incident", encoding="utf-8")
    settings.storage_dir.mkdir(parents=True)
    (settings.storage_dir / "index.json").write_text("{}", encoding="utf-8")
    _patch_lightrag(monkeypatch)
    FakeLightRAG.query_data_payload = {
        "data": {
            "chunks": [
                {
                    "file_path": str(absolute_path),
                    "content": "Restart the worker and clear the failed queue." * 20,
                },
                {
                    "metadata": {"file_path": "runbooks/retry.md"},
                    "text": "Retry processing from the operations console.",
                    "score": 0.42,
                },
            ]
        }
    }

    result = RagEngine(settings).query("Police P-12345 worker queue failure")

    assert result.status == "success"
    assert result.query == "Police P-12345 worker queue failure"
    assert result.answer is None
    assert result.llm_used is False
    assert [source.path for source in result.sources] == ["tickets/incident.md", "runbooks/retry.md"]
    assert result.sources[0].score == 1.0
    assert result.sources[1].score == 0.42
    assert all(0.0 <= source.score <= 1.0 for source in result.sources)
    assert all(source.excerpt for source in result.sources)
    assert len(result.sources[0].excerpt) == 500
    assert FakeLightRAG.instances[0].query_param.mode == "naive"
    assert result.analysis.intent == "Problem"
    assert result.analysis.routing.route == "weiterleiten Policen"
    assert result.analysis.identifiers[0].value == "P-12345"
    assert result.to_dict()["analysis"]["routing"]["route"] == "weiterleiten Policen"


def test_query_limits_sources_to_top_five(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.storage_dir.mkdir(parents=True)
    (settings.storage_dir / "index.json").write_text("{}", encoding="utf-8")
    _patch_lightrag(monkeypatch)
    FakeLightRAG.query_data_payload = {
        "data": {
            "chunks": [
                {"file_path": f"source-{index}.md", "content": f"Content {index}", "score": 1.0 - index * 0.01}
                for index in range(7)
            ]
        }
    }

    result = RagEngine(settings).query("failure")

    rag = FakeLightRAG.instances[0]
    assert rag.query_param.top_k == 5
    assert rag.query_param.chunk_top_k == 5
    assert [source.path for source in result.sources] == [f"source-{index}.md" for index in range(5)]


def test_status_counts_manifest_documents_and_local_vector_chunks(tmp_path) -> None:
    settings = _settings(tmp_path)
    settings.knowledge_dir.mkdir(parents=True)
    settings.storage_dir.mkdir(parents=True)
    (settings.knowledge_dir / "runbook.md").write_text("# Runbook", encoding="utf-8")
    (settings.storage_dir / "ood-manifest.json").write_text(
        json.dumps({"schema_version": 1, "entries": [{"path": "runbook.md"}]}),
        encoding="utf-8",
    )
    (settings.storage_dir / LOCAL_VECTOR_INDEX_FILENAME).write_text(
        json.dumps({"documents": [{"path": "runbook.md"}, {"path": "ticket.md"}]}),
        encoding="utf-8",
    )

    result = RagEngine(settings).status()

    assert result.status == "ready"
    assert result.knowledge_documents == 1
    assert result.indexed_documents == 1
    assert result.chunks == 2
    assert result.storage_files == 2


def test_query_without_llm_credentials_makes_no_cloud_llm_calls(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.storage_dir.mkdir(parents=True)
    (settings.storage_dir / "index.json").write_text("{}", encoding="utf-8")
    _patch_lightrag(monkeypatch)
    FakeLightRAG.query_data_payload = {
        "data": {"chunks": [{"source": "note.md", "chunk": "Local retrieval only."}]}
    }
    monkeypatch.setattr(
        "ood.rag.openai_complete_if_cache",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("cloud LLM called")),
    )

    result = RagEngine(settings).query("local only")

    assert result.answer is None
    assert result.llm_used is False
    assert result.analysis.mode == "deterministic"
    assert FakeLightRAG.instances[0].kwargs["llm_model_func"] is RagEngine._noop_llm_model_func


def test_query_low_confidence_analysis_routes_to_rueckfrage(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.storage_dir.mkdir(parents=True)
    (settings.storage_dir / "index.json").write_text("{}", encoding="utf-8")
    _patch_lightrag(monkeypatch)
    FakeLightRAG.query_data_payload = {"data": {"chunks": []}}

    result = RagEngine(settings).query("Unklare Meldung")

    assert result.analysis.routing.route == "Rückfrage"
    assert "Keine belastbaren Quellen gefunden." in result.analysis.uncertainties
    assert "Niedrige Retrieval-Confidence." in result.analysis.uncertainties


def test_query_before_index_raises_instructional_error(tmp_path) -> None:
    settings = _settings(tmp_path)

    try:
        RagEngine(settings).query("anything")
    except IndexMissingError as exc:
        assert str(exc) == "No index found. Run `ood index` first."
    else:  # pragma: no cover - assertion helper
        raise AssertionError("expected missing index error")


def test_confidence_score_uses_retrieval_signal_and_llm_availability(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.storage_dir.mkdir(parents=True)
    (settings.storage_dir / "index.json").write_text("{}", encoding="utf-8")
    _patch_lightrag(monkeypatch)
    FakeLightRAG.query_data_payload = {
        "data": {
            "chunks": [
                {"file_path": "a.md", "content": "A", "score": 0.9},
                {"file_path": "b.md", "content": "B", "score": 0.6},
                {"file_path": "c.md", "content": "C", "score": 0.2},
            ]
        }
    }

    result = RagEngine(settings).query("failure")

    assert result.confidence.score == 0.92
    assert "limited because no LLM credentials are configured" in result.confidence.rationale


def test_llm_credentials_select_mix_query_mode(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path, llm_api_key=SecretStr("configured"), allow_cloud_llm=True)
    settings.storage_dir.mkdir(parents=True)
    (settings.storage_dir / "index.json").write_text("{}", encoding="utf-8")
    _patch_lightrag(monkeypatch)
    FakeLightRAG.query_data_payload = {
        "data": {"chunks": [{"file_path": "runbook.md", "content": "Use the runbook.", "score": 0.8}]}
    }
    FakeLightRAG.query_answer = "1. Check source evidence.\n2. Restart worker queue."

    result = RagEngine(settings).query("failure rm -rf /tmp/cache")

    rag = FakeLightRAG.instances[0]
    assert rag.query_param.mode == "mix"
    assert rag.answer_param.mode == "mix"
    assert result.answer == "1. Check source evidence.\n2. Restart worker queue."
    assert result.llm_used is True
    assert result.analysis.mode == "llm_grounded"
    assert result.analysis.assessment == result.answer
    assert result.analysis.solution_steps == ["Check source evidence.", "Restart worker queue."]
    assert result.analysis.intent == "Problem"
    assert result.analysis.command_risks[0].risk == "rot"


def test_query_source_origin_command_risks_are_in_analysis(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path)
    settings.storage_dir.mkdir(parents=True)
    (settings.storage_dir / "index.json").write_text("{}", encoding="utf-8")
    _patch_lightrag(monkeypatch)
    FakeLightRAG.query_data_payload = {
        "data": {"chunks": [{"file_path": "runbook.md", "content": "Run kubectl get pods then restart service worker.", "score": 0.9}]}
    }

    result = RagEngine(settings).query("Worker Fehler")

    assert ("runbook.md", "grün") in {(risk.origin, risk.risk) for risk in result.analysis.command_risks}
    assert ("runbook.md", "orange") in {(risk.origin, risk.risk) for risk in result.analysis.command_risks}


def test_llm_credentials_pass_non_noop_lightrag_llm_func_for_query(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path, llm_api_key=SecretStr("configured"), allow_cloud_llm=True)
    settings.storage_dir.mkdir(parents=True)
    (settings.storage_dir / "index.json").write_text("{}", encoding="utf-8")
    _patch_lightrag(monkeypatch)
    FakeLightRAG.query_data_payload = {
        "data": {"chunks": [{"file_path": "runbook.md", "content": "Use the runbook."}]}
    }

    result = RagEngine(settings).query("failure")

    llm_func = FakeLightRAG.instances[0].kwargs["llm_model_func"]
    assert llm_func is not RagEngine._noop_llm_model_func
    assert result.llm_used is True


def test_llm_credentials_without_approval_keep_naive_query_and_no_answer(tmp_path, monkeypatch) -> None:
    settings = _settings(tmp_path, llm_api_key=SecretStr("configured"))
    settings.storage_dir.mkdir(parents=True)
    (settings.storage_dir / "index.json").write_text("{}", encoding="utf-8")
    _patch_lightrag(monkeypatch)
    FakeLightRAG.query_data_payload = {
        "data": {"chunks": [{"file_path": "runbook.md", "content": "Use the runbook.", "score": 0.8}]}
    }
    monkeypatch.setattr(
        "ood.rag.openai_complete_if_cache",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("cloud LLM called")),
    )

    result = RagEngine(settings).query("failure")

    rag = FakeLightRAG.instances[0]
    assert rag.query_param.mode == "naive"
    assert not hasattr(rag, "answer_param")
    assert result.answer is None
    assert result.llm_used is False
    assert result.analysis.mode == "deterministic"
    assert rag.kwargs["llm_model_func"] is RagEngine._noop_llm_model_func
