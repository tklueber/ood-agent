from __future__ import annotations

from pathlib import Path

from ood.mock_corpus import MockCorpusResult, MockDocument, generate_mock_corpus


def _mock_document(path: Path) -> MockDocument:
    return MockDocument(
        path=path,
        title="Police Login Timeout",
        source_type="ticket",
        system="Bestand",
        komponente="Police Login",
        scenario_category="login_timeout",
        routing_target="weiterleiten Policen",
        command_risk="gelb",
        synthetic_id="MOCK-POL-1001",
        tags=("mock", "policen"),
        body="## Szenario\nDer synthetische Login schlägt nach Timeout fehl.",
    )


def test_mock_document_renders_required_metadata_and_visible_warning(tmp_path: Path) -> None:
    document = _mock_document(tmp_path / "tickets" / "mock-pol-1001.md")

    markdown = document.to_markdown(dataset="mock-v1")

    assert markdown.startswith("---\n")
    for line in (
        "mock: true",
        "dataset: mock-v1",
        "synthetic_id: MOCK-POL-1001",
        "source_type: ticket",
        "scenario_category: login_timeout",
        "routing_target: weiterleiten Policen",
        "command_risk: gelb",
        "quelle: OOD synthetic mock corpus",
        "datum: 2026-05-03",
        "status: active",
        "system: Bestand",
        "komponente: Police Login",
        "title: Police Login Timeout",
        "type: ticket",
    ):
        assert line in markdown
    body = markdown.split("---\n", 2)[2]
    assert body.startswith("⚠️ MOCK DATA / SYNTHETIC")
    assert "## Szenario" in body


def test_mock_corpus_result_serializes_paths_and_coverage(tmp_path: Path) -> None:
    result = MockCorpusResult(
        dataset="mock-v1",
        target_dir=tmp_path,
        generated_paths=(tmp_path / "tickets" / "mock-pol-1001.md", tmp_path / "wiki" / "mock-wiki-1001.md"),
        source_types=("ticket", "wiki"),
    )

    payload = result.to_dict()

    assert payload == {
        "dataset": "mock-v1",
        "target_dir": str(tmp_path),
        "document_count": 2,
        "generated_paths": [
            str(tmp_path / "tickets" / "mock-pol-1001.md"),
            str(tmp_path / "wiki" / "mock-wiki-1001.md"),
        ],
        "source_types": ["ticket", "wiki"],
    }


def test_generate_mock_corpus_creates_importable_markdown_files(tmp_path: Path) -> None:
    result = generate_mock_corpus(tmp_path / "knowledge" / "mock" / "v1")

    assert result.dataset == "mock-v1"
    assert result.document_count >= 12
    assert all(path.suffix == ".md" for path in result.generated_paths)
    assert all(path.exists() for path in result.generated_paths)
    for path in result.generated_paths:
        content = path.read_text(encoding="utf-8")
        assert "quelle: OOD synthetic mock corpus" in content
        assert "datum: 2026-05-03" in content
        assert "status: active" in content
        assert "system: " in content
        assert "komponente: " in content
        assert "title: " in content
        assert "type: " in content
        assert content.split("---\n", 2)[2].startswith("⚠️ MOCK DATA / SYNTHETIC")


def test_generate_mock_corpus_covers_required_source_types(tmp_path: Path) -> None:
    result = generate_mock_corpus(tmp_path / "mock-corpus")

    assert set(result.source_types) == {"ticket", "wiki", "jira_bug", "servicenow_case", "runbook", "note"}
    assert {path.parent.name for path in result.generated_paths} >= set(result.source_types)


def test_generate_mock_corpus_uses_only_synthetic_safe_metadata(tmp_path: Path) -> None:
    result = generate_mock_corpus(tmp_path / "mock-corpus")
    combined = "\n".join(path.read_text(encoding="utf-8") for path in result.generated_paths)

    assert "synthetic_id: MOCK-" in combined
    assert "example.com" not in combined
    assert "@" not in combined
    assert "sk-" not in combined
    assert "expected_answer" not in combined
    assert "expected_sources" not in combined
    assert "golden" not in combined.lower()
