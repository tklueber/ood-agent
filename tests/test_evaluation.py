import json
from pathlib import Path

import pytest

from ood.evaluation import EvaluationDatasetError, load_evaluation_dataset
from ood.mock_corpus import generate_mock_corpus


def _write_dataset(path: Path, cases: list[dict[str, object]], *, schema_version: int = 1) -> Path:
    path.write_text(
        json.dumps(
            {
                "schema_version": schema_version,
                "dataset": "mock-v1",
                "cases": cases,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def _case(case_id: str = "case-1", **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": case_id,
        "query": "Police MOCK-POL-1001 bricht beim Login ab",
        "expected_sources": ["ticket/mock-pol-1001.md", "wiki/mock-wiki-5001.md"],
        "forbidden_sources": ["note/mock-note-7002.md"],
        "expected_intent": "Problem",
        "expected_route": "weiterleiten Policen",
        "expected_identifiers": [{"kind": "police", "value": "MOCK-POL-1001"}],
        "expected_command_risks": [{"command_contains": "Session", "risk": "grün"}],
        "expected_uncertainties": [],
    }
    payload.update(overrides)
    return payload


def test_load_evaluation_dataset_returns_typed_cases(tmp_path: Path) -> None:
    dataset_path = _write_dataset(tmp_path / "dataset.json", [_case()])

    dataset = load_evaluation_dataset(dataset_path)

    assert dataset.schema_version == 1
    assert dataset.dataset == "mock-v1"
    assert len(dataset.cases) == 1
    case = dataset.cases[0]
    assert case.id == "case-1"
    assert case.expected_sources == ("ticket/mock-pol-1001.md", "wiki/mock-wiki-5001.md")
    assert case.forbidden_sources == ("note/mock-note-7002.md",)
    assert case.expected_identifiers[0].kind == "police"
    assert case.expected_command_risks[0].risk == "grün"


@pytest.mark.parametrize(
    ("cases", "message"),
    [
        ([_case("duplicate"), _case("duplicate")], "Duplicate case id"),
        ([_case(query="")], "query"),
        ([_case(expected_sources=[])], "expected_sources"),
        ([_case(expected_sources=["/absolute.md"])], "relative"),
        ([_case(forbidden_sources=["../outside.md"])], "traversal"),
    ],
)
def test_load_evaluation_dataset_rejects_malformed_cases(
    tmp_path: Path, cases: list[dict[str, object]], message: str
) -> None:
    dataset_path = _write_dataset(tmp_path / "dataset.json", cases)

    with pytest.raises(EvaluationDatasetError, match=message):
        load_evaluation_dataset(dataset_path)


def test_load_evaluation_dataset_rejects_unknown_schema_version(tmp_path: Path) -> None:
    dataset_path = _write_dataset(tmp_path / "dataset.json", [_case()], schema_version=99)

    with pytest.raises(EvaluationDatasetError, match="schema_version"):
        load_evaluation_dataset(dataset_path)


def test_load_evaluation_dataset_rejects_malformed_json(tmp_path: Path) -> None:
    dataset_path = tmp_path / "dataset.json"
    dataset_path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(EvaluationDatasetError, match="Malformed JSON"):
        load_evaluation_dataset(dataset_path)


def test_load_evaluation_dataset_validates_referenced_knowledge_paths(tmp_path: Path) -> None:
    knowledge_dir = tmp_path / "knowledge"
    (knowledge_dir / "ticket").mkdir(parents=True)
    (knowledge_dir / "ticket" / "mock-pol-1001.md").write_text("mock", encoding="utf-8")
    dataset_path = _write_dataset(tmp_path / "dataset.json", [_case(forbidden_sources=[])])

    with pytest.raises(EvaluationDatasetError, match="wiki/mock-wiki-5001.md"):
        load_evaluation_dataset(dataset_path, knowledge_dir=knowledge_dir)


def test_load_evaluation_dataset_accepts_optional_expected_llm_answer(tmp_path: Path) -> None:
    dataset_path = _write_dataset(
        tmp_path / "dataset.json",
        [_case(expected_llm_answer="Antwort")],
    )

    dataset = load_evaluation_dataset(dataset_path)

    assert dataset.cases[0].expected_llm_answer == "Antwort"


def test_load_evaluation_dataset_defaults_expected_llm_answer_to_none(tmp_path: Path) -> None:
    dataset_path = _write_dataset(tmp_path / "dataset.json", [_case()])

    dataset = load_evaluation_dataset(dataset_path)

    assert dataset.cases[0].expected_llm_answer is None


def test_load_evaluation_dataset_rejects_blank_expected_llm_answer(tmp_path: Path) -> None:
    dataset_path = _write_dataset(
        tmp_path / "dataset.json",
        [_case(expected_llm_answer="")],
    )

    with pytest.raises(EvaluationDatasetError, match="expected_llm_answer"):
        load_evaluation_dataset(dataset_path)


def test_committed_mock_v1_fixture_validates_against_generated_mock_corpus(tmp_path: Path) -> None:
    knowledge_dir = tmp_path / "knowledge"
    generate_mock_corpus(knowledge_dir, dataset="mock-v1")

    dataset = load_evaluation_dataset(Path("evaluation/datasets/mock-v1.json"), knowledge_dir=knowledge_dir)

    assert dataset.schema_version == 1
    assert dataset.dataset == "mock-v1"
    assert len(dataset.cases) >= 4
    routes = {case.expected_route for case in dataset.cases}
    assert {"weiterleiten Policen", "weiterleiten Offerten", "selbst lösen", "Rückfrage"} <= routes
    all_expected_sources = {source for case in dataset.cases for source in case.expected_sources}
    assert "ticket/mock-pol-1001.md" in all_expected_sources
    assert "wiki/mock-wiki-5001.md" in all_expected_sources
    assert "runbook/mock-run-6001.md" in all_expected_sources
    assert "servicenow_case/mock-snow-3001.md" in all_expected_sources
