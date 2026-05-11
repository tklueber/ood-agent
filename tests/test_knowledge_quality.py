from __future__ import annotations

import json
from pathlib import Path

from ood.knowledge_quality import audit_knowledge_corpus


def test_audit_reports_retrieval_readiness_dimensions(tmp_path: Path) -> None:
    corpus = tmp_path / "articles"
    corpus.mkdir()
    (corpus / "traceid.md").write_text(
        "---\n"
        "title: TraceId Kafka finden\n"
        "type: runbook\n"
        "service: Kafka\n"
        "system: AKHQ\n"
        "keywords_de:\n"
        "  - TraceId\n"
        "keywords_en:\n"
        "  - correlation id\n"
        "last_verified: 2026-04-01\n"
        "owner: OOD Team\n"
        "confluence_url: https://example.invalid/page\n"
        "---\n"
        "# TraceId Kafka finden\n"
        "Siehe [[akhq-runbook]].\n\n"
        "## Commands\n"
        "Risk: grün\n"
        "```bash\n"
        "kubectl logs deploy/akhq | grep TraceId\n"
        "```\n",
        encoding="utf-8",
    )
    (corpus / "duplicate.md").write_text(
        "---\ntitle: TraceId Kafka finden\ntype: note\nkb_id: KB-1\n---\nNo links.",
        encoding="utf-8",
    )
    (corpus / "duplicate-id.md").write_text(
        "---\ntitle: Other\ntype: note\nkb_id: KB-1\nlast_verified: 2024-01-01\n---\nNo links.",
        encoding="utf-8",
    )

    report = audit_knowledge_corpus(corpus, expected_documents=438)
    payload = report.to_dict()

    assert payload["document_count"] == 3
    assert payload["expected_documents"] == 438
    assert payload["expected_document_mismatch"] is True
    assert payload["field_coverage"]["title"]["present"] == 3
    assert payload["field_coverage"]["keywords"]["present"] == 1
    assert payload["link_counts"]["outgoing"] == 1
    assert payload["command_coverage"]["documents_with_commands"] == 1
    assert payload["command_coverage"]["documents_with_risk_marker"] == 1
    assert payload["duplicates"]["titles"][0]["value"] == "TraceId Kafka finden"
    assert payload["duplicates"]["kb_ids"][0]["value"] == "KB-1"
    assert payload["source_attribution"]["documents_with_source"] == 1
    assert payload["freshness"]["stale_documents"] >= 1
    assert payload["document_issues"]
    json.dumps(payload)


def test_empty_corpus_returns_warning_recommendation(tmp_path: Path) -> None:
    report = audit_knowledge_corpus(tmp_path / "missing")

    assert report.document_count == 0
    assert report.recommendations[0].severity == "warning"
    assert "No Markdown documents" in report.recommendations[0].reason


def test_traceid_article_recommendations_are_actionable(tmp_path: Path) -> None:
    corpus = tmp_path / "articles"
    corpus.mkdir()
    (corpus / "how-to-find-traceid-in-kafka-message.md").write_text(
        "---\n"
        "title: TraceId Kafka\n"
        "type: runbook\n"
        "service: Kafka\n"
        "keywords: TraceId\n"
        "---\n"
        "TraceId Kafka AKHQ Ersatzgeschäft.\n",
        encoding="utf-8",
    )

    report = audit_knowledge_corpus(corpus)
    suggestions = "\n".join(recommendation.suggestion for recommendation in report.recommendations)

    assert "aliases" in suggestions
    assert "trace id" in suggestions
    assert "correlation id" in suggestions
    assert "Kafka message" in suggestions
    assert "AKHQ" in suggestions
    assert "Ersatzgeschäft" in suggestions
    assert "last_verified" in suggestions
    assert "owner" in suggestions


def test_corpus_level_recommendations_flag_low_metadata_coverage(tmp_path: Path) -> None:
    corpus = tmp_path / "articles"
    corpus.mkdir()
    for index in range(3):
        (corpus / f"note-{index}.md").write_text(f"# Note {index}\nNo metadata.", encoding="utf-8")

    report = audit_knowledge_corpus(corpus)
    corpus_recommendations = [rec for rec in report.recommendations if rec.path is None]

    assert any("keywords" in rec.suggestion for rec in corpus_recommendations)
    assert any("service/system" in rec.suggestion for rec in corpus_recommendations)
