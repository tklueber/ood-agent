from __future__ import annotations

import hashlib
import inspect
import json
import re
from pathlib import Path
from typing import Any

import pytest

from ood import eval_runner
from ood.config import Settings
from ood.eval_runner import (
    EvalCaseResult,
    EvalRunner,
    EvalRunnerError,
    EvalRunResult,
    SCHEMA_VERSION,
)
from ood.evaluation import (
    EvaluationCase,
    EvaluationDataset,
    ExpectedCommandRisk,
    ExpectedIdentifier,
)
from ood.models import (
    CommandRisk,
    ConfidenceScore,
    IndexMissingError,
    QueryResult,
    RetrievalDiagnostics,
    RoutingDecision,
    SourceHit,
    TicketAnalysis,
    TicketIdentifier,
)


# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


def _make_case(
    *,
    case_id: str = "case-1",
    query: str = "Police MOCK-POL-1001 bricht beim Login ab.",
    expected_sources: tuple[str, ...] = ("ticket/mock-pol-1001.md",),
    forbidden_sources: tuple[str, ...] = (),
    expected_intent: str = "Problem",
    expected_route: str = "weiterleiten Policen",
    expected_identifiers: tuple[ExpectedIdentifier, ...] = (
        ExpectedIdentifier(kind="police", value="MOCK-POL-1001"),
    ),
    expected_command_risks: tuple[ExpectedCommandRisk, ...] = (),
    expected_uncertainties: tuple[str, ...] = (),
    expected_llm_answer: str | None = None,
) -> EvaluationCase:
    return EvaluationCase(
        id=case_id,
        query=query,
        expected_sources=expected_sources,
        forbidden_sources=forbidden_sources,
        expected_intent=expected_intent,
        expected_route=expected_route,
        expected_identifiers=expected_identifiers,
        expected_command_risks=expected_command_risks,
        expected_uncertainties=expected_uncertainties,
        expected_llm_answer=expected_llm_answer,
    )


def _make_dataset(cases: tuple[EvaluationCase, ...]) -> EvaluationDataset:
    return EvaluationDataset(schema_version=1, dataset="mock-v1", cases=cases)


def _write_dataset_file(path: Path, dataset: EvaluationDataset) -> Path:
    payload = {
        "schema_version": dataset.schema_version,
        "dataset": dataset.dataset,
        "cases": [
            {
                "id": case.id,
                "query": case.query,
                "expected_sources": list(case.expected_sources),
                "forbidden_sources": list(case.forbidden_sources),
                "expected_intent": case.expected_intent,
                "expected_route": case.expected_route,
                "expected_identifiers": [
                    {"kind": identifier.kind, "value": identifier.value}
                    for identifier in case.expected_identifiers
                ],
                "expected_command_risks": [
                    {"command_contains": risk.command_contains, "risk": risk.risk}
                    for risk in case.expected_command_risks
                ],
                "expected_uncertainties": list(case.expected_uncertainties),
                **(
                    {"expected_llm_answer": case.expected_llm_answer}
                    if case.expected_llm_answer is not None
                    else {}
                ),
            }
            for case in dataset.cases
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _make_passing_query_result(
    case: EvaluationCase,
    *,
    llm_used: bool = False,
    backend: str = "local_vector_graph_index",
) -> QueryResult:
    sources = [
        SourceHit(path=path, score=round(1.0 - 0.1 * index, 2), excerpt=f"excerpt for {path}")
        for index, path in enumerate(case.expected_sources)
    ]
    identifiers = [
        TicketIdentifier(kind=expected.kind, value=expected.value, confidence=0.9, evidence="test")
        for expected in case.expected_identifiers
    ]
    command_risks = [
        CommandRisk(
            command=f"{expected.command_contains} something",
            risk=expected.risk,
            rationale="test",
            origin="ticket",
        )
        for expected in case.expected_command_risks
    ]
    uncertainties = list(case.expected_uncertainties)
    analysis = TicketAnalysis(
        intent=case.expected_intent,
        assessment=None,
        solution_steps=[],
        routing=RoutingDecision(route=case.expected_route, rationale="test"),
        identifiers=identifiers,
        command_risks=command_risks,
        uncertainties=uncertainties,
        mode="deterministic",
    )
    return QueryResult(
        query=case.query,
        answer="answer" if llm_used else None,
        confidence=ConfidenceScore(score=0.9, rationale="test"),
        sources=sources,
        llm_used=llm_used,
        status="success" if sources else "no_results",
        analysis=analysis,
        retrieval_diagnostics=RetrievalDiagnostics(backend=backend, strategy="hybrid"),
    )


def _make_failing_query_result(case: EvaluationCase) -> QueryResult:
    # Wrong sources + wrong intent + wrong routing
    sources = [
        SourceHit(path="wrong/source.md", score=0.4, excerpt="unrelated excerpt"),
    ]
    analysis = TicketAnalysis(
        intent="Unklar",
        assessment=None,
        solution_steps=[],
        routing=RoutingDecision(route="Rückfrage", rationale="test"),
        identifiers=[],
        command_risks=[],
        uncertainties=[],
        mode="deterministic",
    )
    return QueryResult(
        query=case.query,
        answer=None,
        confidence=ConfidenceScore(score=0.2, rationale="test"),
        sources=sources,
        llm_used=False,
        status="success",
        analysis=analysis,
        retrieval_diagnostics=RetrievalDiagnostics(backend="local_vector_index", strategy="hybrid"),
    )


def _settings(tmp_path: Path, **overrides: object) -> Settings:
    base: dict[str, object] = {
        "knowledge_dir": tmp_path / "knowledge",
        "data_dir": tmp_path / "data",
        "storage_dir": tmp_path / "storage",
    }
    base.update(overrides)
    return Settings(**base)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_run_returns_passed_case_for_perfect_match(monkeypatch, tmp_path: Path) -> None:
    case = _make_case()
    dataset = _make_dataset((case,))
    dataset_path = _write_dataset_file(tmp_path / "dataset.json", dataset)

    monkeypatch.setattr(eval_runner.RagEngine, "__init__", lambda self, settings: setattr(self, "settings", settings))
    monkeypatch.setattr(
        eval_runner.RagEngine,
        "query",
        lambda self, query_text: _make_passing_query_result(case),
    )

    settings = _settings(tmp_path)
    result = EvalRunner(settings).run(dataset, dataset_path=dataset_path)

    assert isinstance(result, EvalRunResult)
    assert len(result.cases) == 1
    case_result = result.cases[0]
    assert case_result.status == "passed"
    assert case_result.skip_reason is None
    assert case_result.error is None
    assert case_result.retrieval_metrics is not None
    assert case_result.ticket_metrics is not None
    assert result.summary.passed_count == 1
    assert result.summary.failed_count == 0
    assert result.summary.case_count_aggregated == 1


def test_run_returns_failed_case_when_metrics_miss(monkeypatch, tmp_path: Path) -> None:
    case = _make_case()
    dataset = _make_dataset((case,))
    dataset_path = _write_dataset_file(tmp_path / "dataset.json", dataset)

    monkeypatch.setattr(eval_runner.RagEngine, "__init__", lambda self, settings: setattr(self, "settings", settings))
    monkeypatch.setattr(
        eval_runner.RagEngine,
        "query",
        lambda self, query_text: _make_failing_query_result(case),
    )

    settings = _settings(tmp_path)
    result = EvalRunner(settings).run(dataset, dataset_path=dataset_path)

    assert len(result.cases) == 1
    case_result = result.cases[0]
    assert case_result.status == "failed"
    assert case_result.retrieval_metrics is not None
    assert case_result.ticket_metrics is not None
    assert result.summary.passed_count == 0
    assert result.summary.failed_count == 1
    assert result.summary.case_count_aggregated == 1


def test_run_skips_case_with_expected_llm_answer_when_no_credentials(
    monkeypatch, tmp_path: Path
) -> None:
    case = _make_case(expected_llm_answer="Antwort")
    other_case = _make_case(case_id="case-2")
    dataset = _make_dataset((case, other_case))
    dataset_path = _write_dataset_file(tmp_path / "dataset.json", dataset)

    monkeypatch.setattr(eval_runner.RagEngine, "__init__", lambda self, settings: setattr(self, "settings", settings))
    monkeypatch.setattr(
        eval_runner.RagEngine,
        "query",
        lambda self, query_text: _make_passing_query_result(other_case),
    )

    settings = _settings(tmp_path)
    assert settings.has_llm_credentials is False
    result = EvalRunner(settings).run(dataset, dataset_path=dataset_path)

    skipped = next(c for c in result.cases if c.case_id == "case-1")
    assert skipped.status == "skipped"
    assert skipped.skip_reason == "llm_required"
    assert skipped.retrieval_metrics is None
    assert skipped.ticket_metrics is None
    assert result.summary.skipped_count == 1
    assert result.summary.case_count_aggregated == 1


def test_run_includes_llm_case_when_credentials_present(monkeypatch, tmp_path: Path) -> None:
    case = _make_case(expected_llm_answer="Antwort")
    dataset = _make_dataset((case,))
    dataset_path = _write_dataset_file(tmp_path / "dataset.json", dataset)

    monkeypatch.setattr(eval_runner.RagEngine, "__init__", lambda self, settings: setattr(self, "settings", settings))
    monkeypatch.setattr(
        eval_runner.RagEngine,
        "query",
        lambda self, query_text: _make_passing_query_result(case, llm_used=True),
    )

    settings = _settings(tmp_path, llm_api_key="sk-test", allow_cloud_llm=False)
    assert settings.has_llm_credentials is True
    result = EvalRunner(settings).run(dataset, dataset_path=dataset_path)

    assert len(result.cases) == 1
    case_result = result.cases[0]
    assert case_result.status in {"passed", "failed"}
    assert case_result.status != "skipped"
    assert result.summary.skipped_count == 0


def test_run_uses_llm_when_credentials_present_even_without_allow_cloud_llm(
    monkeypatch, tmp_path: Path
) -> None:
    case = _make_case()
    dataset = _make_dataset((case,))
    dataset_path = _write_dataset_file(tmp_path / "dataset.json", dataset)

    captured: dict[str, Settings] = {}

    def fake_init(self, settings: Settings) -> None:
        captured["settings"] = settings
        self.settings = settings

    monkeypatch.setattr(eval_runner.RagEngine, "__init__", fake_init)
    monkeypatch.setattr(
        eval_runner.RagEngine,
        "query",
        lambda self, query_text: _make_passing_query_result(case, llm_used=True),
    )

    user_settings = _settings(tmp_path, llm_api_key="sk-test", allow_cloud_llm=False)
    EvalRunner(user_settings).run(dataset, dataset_path=dataset_path)

    forged = captured["settings"]
    assert forged.allow_cloud_llm is True
    assert forged.can_use_cloud_llm is True
    # Caller's settings is not mutated.
    assert user_settings.allow_cloud_llm is False


def test_run_does_not_force_llm_without_credentials(monkeypatch, tmp_path: Path) -> None:
    case = _make_case()
    dataset = _make_dataset((case,))
    dataset_path = _write_dataset_file(tmp_path / "dataset.json", dataset)

    captured: dict[str, Settings] = {}

    def fake_init(self, settings: Settings) -> None:
        captured["settings"] = settings
        self.settings = settings

    monkeypatch.setattr(eval_runner.RagEngine, "__init__", fake_init)
    monkeypatch.setattr(
        eval_runner.RagEngine,
        "query",
        lambda self, query_text: _make_passing_query_result(case),
    )

    user_settings = _settings(tmp_path, llm_api_key=None, allow_cloud_llm=False)
    EvalRunner(user_settings).run(dataset, dataset_path=dataset_path)

    forged = captured["settings"]
    assert forged.allow_cloud_llm is False
    assert forged.can_use_cloud_llm is False


def test_engine_settings_helper_returns_unchanged_when_no_credentials(tmp_path: Path) -> None:
    settings = _settings(tmp_path, llm_api_key=None, allow_cloud_llm=False)
    returned = EvalRunner._engine_settings(settings)
    assert returned is settings


def test_engine_settings_helper_forges_allow_cloud_llm_when_credentials_present(
    tmp_path: Path,
) -> None:
    settings = _settings(tmp_path, llm_api_key="sk-test", allow_cloud_llm=False)
    returned = EvalRunner._engine_settings(settings)
    assert returned is not settings
    assert returned.allow_cloud_llm is True
    assert returned.can_use_cloud_llm is True
    # Caller's settings is untouched.
    assert settings.allow_cloud_llm is False


def test_run_does_not_consult_allow_cloud_llm_in_business_logic() -> None:
    source = inspect.getsource(eval_runner)

    # `can_use_cloud_llm` must never appear in this module's source.
    assert "can_use_cloud_llm" not in source

    # `allow_cloud_llm` is allowed ONLY inside the `_engine_settings` helper.
    # Strip the body of that function and assert it is absent elsewhere.
    helper_match = re.search(
        r"def _engine_settings\([^)]*\)[^:]*:\n((?:[ \t]+.*\n)+)",
        source,
    )
    assert helper_match is not None, "Expected to find _engine_settings helper definition."
    helper_start, helper_end = helper_match.span(1)
    before_helper = source[:helper_start]
    after_helper = source[helper_end:]

    assert "allow_cloud_llm" not in before_helper, (
        "allow_cloud_llm referenced outside _engine_settings (before helper)"
    )
    assert "allow_cloud_llm" not in after_helper, (
        "allow_cloud_llm referenced outside _engine_settings (after helper)"
    )


def test_run_marks_case_errored_on_query_exception_and_continues(
    monkeypatch, tmp_path: Path
) -> None:
    case_1 = _make_case(case_id="case-1")
    case_2 = _make_case(case_id="case-2")
    case_3 = _make_case(case_id="case-3")
    dataset = _make_dataset((case_1, case_2, case_3))
    dataset_path = _write_dataset_file(tmp_path / "dataset.json", dataset)

    call_log: list[str] = []

    def fake_query(self, query_text: str) -> QueryResult:
        # Match by query text since all three share the same default query.
        # We bounce on call index to mimic case-1 only.
        call_log.append(query_text)
        if len(call_log) == 1:
            raise RuntimeError("boom")
        # The mapping from query to case is ambiguous if all queries are
        # identical; use the call sequence to pick a passing case.
        return _make_passing_query_result(case_2)

    monkeypatch.setattr(eval_runner.RagEngine, "__init__", lambda self, settings: setattr(self, "settings", settings))
    monkeypatch.setattr(eval_runner.RagEngine, "query", fake_query)

    settings = _settings(tmp_path)
    result = EvalRunner(settings).run(dataset, dataset_path=dataset_path)

    errored = next(c for c in result.cases if c.case_id == "case-1")
    assert errored.status == "errored"
    assert errored.error is not None
    assert "boom" in errored.error
    assert errored.retrieval_metrics is None

    remaining = [c for c in result.cases if c.case_id in {"case-2", "case-3"}]
    assert len(remaining) == 2
    assert all(c.status in {"passed", "failed"} for c in remaining)

    assert result.summary.errored_count == 1
    assert result.summary.case_count_aggregated == 2


def test_run_propagates_index_missing_error(monkeypatch, tmp_path: Path) -> None:
    case = _make_case()
    dataset = _make_dataset((case,))
    dataset_path = _write_dataset_file(tmp_path / "dataset.json", dataset)

    def raise_index_missing(self, query_text: str) -> QueryResult:
        raise IndexMissingError("No index found. Run `ood index` first.")

    monkeypatch.setattr(eval_runner.RagEngine, "__init__", lambda self, settings: setattr(self, "settings", settings))
    monkeypatch.setattr(eval_runner.RagEngine, "query", raise_index_missing)

    settings = _settings(tmp_path)
    with pytest.raises(IndexMissingError):
        EvalRunner(settings).run(dataset, dataset_path=dataset_path)


def test_run_meta_includes_dataset_hash_and_iso_timestamps(monkeypatch, tmp_path: Path) -> None:
    case = _make_case()
    dataset = _make_dataset((case,))
    dataset_path = _write_dataset_file(tmp_path / "dataset.json", dataset)

    monkeypatch.setattr(eval_runner.RagEngine, "__init__", lambda self, settings: setattr(self, "settings", settings))
    monkeypatch.setattr(
        eval_runner.RagEngine,
        "query",
        lambda self, query_text: _make_passing_query_result(case),
    )

    settings = _settings(tmp_path)
    result = EvalRunner(settings).run(dataset, dataset_path=dataset_path)

    expected_hash = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    assert result.meta.dataset_hash == expected_hash
    iso_re = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
    assert iso_re.match(result.meta.run_started_at)
    assert iso_re.match(result.meta.run_finished_at)
    assert result.meta.schema_version == SCHEMA_VERSION
    assert result.meta.dataset == "mock-v1"
    assert result.meta.dataset_path == str(dataset_path)


def test_run_filter_by_case_id_executes_only_that_case(monkeypatch, tmp_path: Path) -> None:
    case_1 = _make_case(case_id="case-1")
    case_2 = _make_case(case_id="case-2")
    case_3 = _make_case(case_id="case-3")
    dataset = _make_dataset((case_1, case_2, case_3))
    dataset_path = _write_dataset_file(tmp_path / "dataset.json", dataset)

    monkeypatch.setattr(eval_runner.RagEngine, "__init__", lambda self, settings: setattr(self, "settings", settings))
    monkeypatch.setattr(
        eval_runner.RagEngine,
        "query",
        lambda self, query_text: _make_passing_query_result(case_2),
    )

    settings = _settings(tmp_path)
    result = EvalRunner(settings).run(dataset, dataset_path=dataset_path, case_id="case-2")

    assert len(result.cases) == 1
    assert result.cases[0].case_id == "case-2"
    assert result.summary.case_count_aggregated == 1


def test_run_unknown_case_id_raises_eval_runner_error(monkeypatch, tmp_path: Path) -> None:
    case = _make_case()
    dataset = _make_dataset((case,))
    dataset_path = _write_dataset_file(tmp_path / "dataset.json", dataset)

    monkeypatch.setattr(eval_runner.RagEngine, "__init__", lambda self, settings: setattr(self, "settings", settings))
    monkeypatch.setattr(
        eval_runner.RagEngine,
        "query",
        lambda self, query_text: _make_passing_query_result(case),
    )

    settings = _settings(tmp_path)
    with pytest.raises(EvalRunnerError, match="missing"):
        EvalRunner(settings).run(dataset, dataset_path=dataset_path, case_id="missing")


def test_run_summary_llm_used_reflects_any_case_llm_used(monkeypatch, tmp_path: Path) -> None:
    case_1 = _make_case(case_id="case-1")
    case_2 = _make_case(case_id="case-2")
    dataset = _make_dataset((case_1, case_2))
    dataset_path = _write_dataset_file(tmp_path / "dataset.json", dataset)

    call_count = {"n": 0}

    def fake_query(self, query_text: str) -> QueryResult:
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _make_passing_query_result(case_1, llm_used=True)
        return _make_passing_query_result(case_2, llm_used=False)

    monkeypatch.setattr(eval_runner.RagEngine, "__init__", lambda self, settings: setattr(self, "settings", settings))
    monkeypatch.setattr(eval_runner.RagEngine, "query", fake_query)

    settings = _settings(tmp_path, llm_api_key="sk-test")
    result = EvalRunner(settings).run(dataset, dataset_path=dataset_path)

    assert result.summary.llm_used is True
    assert result.meta.llm_used is True


def test_run_meta_retrieval_backend_uses_first_non_skipped_case(
    monkeypatch, tmp_path: Path
) -> None:
    case = _make_case()
    dataset = _make_dataset((case,))
    dataset_path = _write_dataset_file(tmp_path / "dataset.json", dataset)

    monkeypatch.setattr(eval_runner.RagEngine, "__init__", lambda self, settings: setattr(self, "settings", settings))
    monkeypatch.setattr(
        eval_runner.RagEngine,
        "query",
        lambda self, query_text: _make_passing_query_result(case, backend="local_vector_graph_index"),
    )

    settings = _settings(tmp_path)
    result = EvalRunner(settings).run(dataset, dataset_path=dataset_path)

    assert result.meta.retrieval_backend == "local_vector_graph_index"


def test_run_uses_public_engine_query_contract(monkeypatch, tmp_path: Path) -> None:
    """EvalRunner must dispatch via engine.query and capture full QueryResult.to_dict()."""

    case = _make_case()
    dataset = _make_dataset((case,))
    dataset_path = _write_dataset_file(tmp_path / "dataset.json", dataset)

    received: dict[str, Any] = {}

    def fake_query(self, query_text: str) -> QueryResult:
        received["query_text"] = query_text
        return _make_passing_query_result(case)

    monkeypatch.setattr(eval_runner.RagEngine, "__init__", lambda self, settings: setattr(self, "settings", settings))
    monkeypatch.setattr(eval_runner.RagEngine, "query", fake_query)

    settings = _settings(tmp_path)
    result = EvalRunner(settings).run(dataset, dataset_path=dataset_path)

    assert received["query_text"] == case.query
    case_result = result.cases[0]
    assert case_result.query_result is not None
    # The full QueryResult.to_dict() payload is captured, including diagnostics.
    assert "retrieval_diagnostics" in case_result.query_result
    assert "analysis" in case_result.query_result
    assert "sources" in case_result.query_result
