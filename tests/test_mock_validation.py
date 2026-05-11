from __future__ import annotations

import json
from pathlib import Path

from ood.mock_validation import MockCoverageSummary, MockSafetyFinding, validate_mock_corpus


def _write_doc(path: Path, *, extra_frontmatter: str = "", body: str = "Synthetic body.") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        "mock: true\n"
        "dataset: mock-v1\n"
        "synthetic_id: MOCK-TEST-1001\n"
        "source_type: ticket\n"
        "scenario_category: login_timeout\n"
        "routing_target: weiterleiten Policen\n"
        "command_risk: gelb\n"
        "quelle: OOD synthetic mock corpus\n"
        "datum: 2026-05-03\n"
        "status: active\n"
        "system: Bestand\n"
        "komponente: Police Login\n"
        "title: Mock Ticket\n"
        "type: ticket\n"
        f"{extra_frontmatter}"
        "---\n"
        "⚠️ MOCK DATA / SYNTHETIC: Test content only.\n\n"
        f"{body}",
        encoding="utf-8",
    )


def test_validator_flags_missing_mock_markers(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    path = corpus / "bad.md"
    path.write_text(
        "---\nquelle: Wiki\ndatum: 2026-05-03\nstatus: active\nsystem: Bestand\nkomponente: Login\ntitle: Bad\ntype: ticket\n---\nNo warning.",
        encoding="utf-8",
    )

    result = validate_mock_corpus(corpus)

    codes = {finding.code for finding in result.findings}
    assert {"missing_mock_true", "missing_dataset", "missing_synthetic_id", "missing_visible_warning"} <= codes
    assert all(finding.path == path for finding in result.findings)
    assert any("Add `mock: true`" in finding.message for finding in result.findings)
    assert result.is_safe is False


def test_validator_flags_suspicious_real_data_and_secrets(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    _write_doc(
        corpus / "unsafe.md",
        body="Contact max.mustermann@firma.de, token sk-test-abcdefghijklmnopqrstuvwxyz, IBAN DE89370400440532013000, phone +49 761 1234567, INC0012345 and PROJ-123.",
    )

    result = validate_mock_corpus(corpus)

    codes = {finding.code for finding in result.findings}
    assert {"suspicious_email", "suspicious_api_token", "suspicious_iban", "suspicious_phone", "non_mock_identifier"} <= codes


def test_validator_flags_golden_answer_leakage(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    _write_doc(
        corpus / "golden.md",
        extra_frontmatter="expected_answer: do not index\n",
        body="This contains expected_sources and golden evaluation labels.",
    )

    result = validate_mock_corpus(corpus)

    codes = {finding.code for finding in result.findings}
    assert "golden_leakage" in codes
    assert result.is_safe is False


def test_validator_aggregates_coverage_dimensions(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    _write_doc(corpus / "ticket.md")
    _write_doc(
        corpus / "runbook.md",
        extra_frontmatter=(
            "synthetic_id: MOCK-RUN-1002\n"
            "source_type: runbook\n"
            "scenario_category: queue_check\n"
            "routing_target: selbst lösen\n"
            "command_risk: orange\n"
            "system: DMS\n"
            "komponente: Versandqueue\n"
            "type: runbook\n"
        ),
    )

    result = validate_mock_corpus(corpus)

    assert result.coverage.source_types == {"runbook": 1, "ticket": 1}
    assert result.coverage.systems == {"Bestand": 1, "DMS": 1}
    assert result.coverage.components == {"Police Login": 1, "Versandqueue": 1}
    assert result.coverage.routing_targets == {"selbst lösen": 1, "weiterleiten Policen": 1}
    assert result.coverage.command_risks == {"gelb": 1, "orange": 1}
    assert result.coverage.scenario_categories == {"login_timeout": 1, "queue_check": 1}


def test_validation_result_serializes_coverage_and_findings(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    _write_doc(corpus / "ticket.md")

    payload = validate_mock_corpus(corpus).to_dict()

    assert payload["document_count"] == 1
    assert payload["is_safe"] is True
    assert payload["findings"] == []
    assert payload["coverage"]["source_types"] == {"ticket": 1}
    json.dumps(payload)


def test_empty_or_missing_corpus_returns_warning_and_zero_coverage(tmp_path: Path) -> None:
    result = validate_mock_corpus(tmp_path / "missing")

    assert result.document_count == 0
    assert result.is_safe is True
    assert result.coverage == MockCoverageSummary.empty()
    assert [finding.code for finding in result.findings] == ["empty_corpus"]
    assert result.to_dict()["findings"][0]["severity"] == "warning"
