from __future__ import annotations

import json

import pytest

from ood.eval_report import build_json_report, dump_json_report
from ood.eval_runner import (
    EvalCaseResult,
    EvalRunMeta,
    EvalRunResult,
    EvalRunSummary,
    SCHEMA_VERSION,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_meta(*, llm_used: bool = False) -> EvalRunMeta:
    return EvalRunMeta(
        schema_version=SCHEMA_VERSION,
        run_started_at="2026-05-10T16:39:04Z",
        run_finished_at="2026-05-10T16:39:42Z",
        llm_used=llm_used,
        retrieval_backend="local_vector_graph_index",
        dataset="mock-v1",
        dataset_path="evaluation/datasets/mock-v1.json",
        dataset_hash="deadbeef" * 8,
        command_args=("eval", "run"),
    )


def _make_summary(
    *,
    case_count_total: int = 1,
    case_count_aggregated: int = 1,
    passed_count: int = 1,
    failed_count: int = 0,
    skipped_count: int = 0,
    errored_count: int = 0,
    llm_used: bool = False,
) -> EvalRunSummary:
    return EvalRunSummary(
        case_count_total=case_count_total,
        case_count_aggregated=case_count_aggregated,
        passed_count=passed_count,
        failed_count=failed_count,
        skipped_count=skipped_count,
        errored_count=errored_count,
        llm_used=llm_used,
        retrieval={
            "case_count": case_count_aggregated,
            "Hit@1": 1.0,
            "Hit@3": 1.0,
            "Hit@5": 1.0,
            "mrr": 1.0,
            "source_recall": 1.0,
            "forbidden_source_rate": 0.0,
        },
        ticket_intelligence={
            "case_count": case_count_aggregated,
            "intent_accuracy": 1.0,
            "routing_accuracy": 1.0,
            "identifier_recall": 1.0,
            "command_risk_accuracy": 1.0,
            "uncertainty_accuracy": 1.0,
        },
    )


def _make_passed_case(
    *,
    case_id: str = "case-1",
    llm_used: bool = False,
    query: str = "Police MOCK-POL-1001 bricht beim Login ab.",
) -> EvalCaseResult:
    return EvalCaseResult(
        case_id=case_id,
        query=query,
        status="passed",
        skip_reason=None,
        error=None,
        llm_used=llm_used,
        query_result={
            "query": query,
            "answer": "Antwort aus Excerpts",
            "confidence": {"score": 0.92, "label": "hoch"},
            "sources": [{"path": "ticket/mock-pol-1001.md", "score": 0.92}],
            "llm_used": llm_used,
            "status": "answered",
            "analysis": {"intent": "Problem", "route": "weiterleiten Policen"},
            "retrieval_diagnostics": {"backend": "local_vector_graph_index"},
        },
        retrieval_metrics={
            "case_id": case_id,
            "Hit@1": True,
            "Hit@3": True,
            "Hit@5": True,
            "mrr": 1.0,
            "source_recall": 1.0,
            "forbidden_hit": False,
            "forbidden_hit_paths": [],
            "first_relevant_rank": 1,
        },
        ticket_metrics={
            "case_id": case_id,
            "intent_match": True,
            "routing_match": True,
            "identifier_recall": 1.0,
            "command_risk_accuracy": 1.0,
            "uncertainty_match": True,
            "missing_identifiers": [],
            "missing_command_risks": [],
            "missing_uncertainties": [],
        },
        expected_sources=("ticket/mock-pol-1001.md", "wiki/mock-wiki-5001.md"),
        forbidden_sources=("note/mock-note-7002.md",),
        actual_sources=(
            {"path": "ticket/mock-pol-1001.md", "score": 0.92},
            {"path": "wiki/mock-wiki-5001.md", "score": 0.81},
        ),
        expected_llm_answer=None,
    )


def _make_skipped_case(case_id: str = "case-skip") -> EvalCaseResult:
    return EvalCaseResult(
        case_id=case_id,
        query="Bitte Cloud-LLM Antwort liefern.",
        status="skipped",
        skip_reason="llm_required",
        error=None,
        llm_used=False,
        query_result=None,
        retrieval_metrics=None,
        ticket_metrics=None,
        expected_sources=("ticket/mock-pol-2002.md",),
        forbidden_sources=(),
        actual_sources=(),
        expected_llm_answer="Erwartete LLM-Antwort.",
    )


def _make_errored_case(case_id: str = "case-error") -> EvalCaseResult:
    return EvalCaseResult(
        case_id=case_id,
        query="Diese Query bringt RagEngine zum Absturz.",
        status="errored",
        skip_reason=None,
        error="Traceback (most recent call last):\n  File ...\nRuntimeError: boom",
        llm_used=False,
        query_result=None,
        retrieval_metrics=None,
        ticket_metrics=None,
        expected_sources=("ticket/mock-pol-3003.md",),
        forbidden_sources=(),
        actual_sources=(),
        expected_llm_answer=None,
    )


def _make_result(
    *,
    cases: tuple[EvalCaseResult, ...] | None = None,
    meta: EvalRunMeta | None = None,
    summary: EvalRunSummary | None = None,
) -> EvalRunResult:
    cases = cases if cases is not None else (_make_passed_case(),)
    meta = meta if meta is not None else _make_meta()
    summary = summary if summary is not None else _make_summary()
    return EvalRunResult(meta=meta, summary=summary, cases=cases)


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


def test_build_json_report_returns_top_level_schema_version_1() -> None:
    report = build_json_report(_make_result())

    assert report["schema_version"] == 1
    assert report["meta"]["schema_version"] == 1


def test_build_json_report_meta_contains_required_fields() -> None:
    report = build_json_report(_make_result())

    assert set(report["meta"].keys()) == {
        "schema_version",
        "run_started_at",
        "run_finished_at",
        "llm_used",
        "retrieval_backend",
        "dataset",
        "dataset_path",
        "dataset_hash",
        "command_args",
    }


def test_build_json_report_summary_contains_required_fields() -> None:
    report = build_json_report(_make_result())

    assert set(report["summary"].keys()) == {
        "case_count_total",
        "case_count_aggregated",
        "passed_count",
        "failed_count",
        "skipped_count",
        "errored_count",
        "llm_used",
        "retrieval",
        "ticket_intelligence",
    }


def test_build_json_report_case_contains_required_fields() -> None:
    report = build_json_report(_make_result())

    assert set(report["cases"][0].keys()) == {
        "case_id",
        "query",
        "status",
        "skip_reason",
        "error",
        "llm_used",
        "expected_sources",
        "forbidden_sources",
        "actual_sources",
        "expected_llm_answer",
        "retrieval_metrics",
        "ticket_metrics",
        "query_result",
    }


def test_build_json_report_propagates_llm_used_at_three_levels() -> None:
    result = _make_result(
        meta=_make_meta(llm_used=True),
        summary=_make_summary(llm_used=True),
        cases=(_make_passed_case(llm_used=True),),
    )

    report = build_json_report(result)

    assert report["meta"]["llm_used"] is True
    assert report["summary"]["llm_used"] is True
    assert report["cases"][0]["llm_used"] is True


def test_build_json_report_skipped_case_has_null_metrics() -> None:
    skipped = _make_skipped_case()
    result = _make_result(
        cases=(_make_passed_case(), skipped),
        summary=_make_summary(
            case_count_total=2,
            case_count_aggregated=1,
            passed_count=1,
            failed_count=0,
            skipped_count=1,
            errored_count=0,
        ),
    )

    report = build_json_report(result)

    serialized = json.dumps(report, ensure_ascii=False)
    parsed = json.loads(serialized)

    skipped_payload = parsed["cases"][1]
    assert skipped_payload["status"] == "skipped"
    assert skipped_payload["skip_reason"] == "llm_required"
    assert skipped_payload["retrieval_metrics"] is None
    assert skipped_payload["ticket_metrics"] is None
    assert skipped_payload["query_result"] is None
    assert skipped_payload["actual_sources"] == []


def test_build_json_report_errored_case_includes_error_field() -> None:
    errored = _make_errored_case()
    result = _make_result(
        cases=(_make_passed_case(), errored),
        summary=_make_summary(
            case_count_total=2,
            case_count_aggregated=1,
            passed_count=1,
            failed_count=0,
            skipped_count=0,
            errored_count=1,
        ),
    )

    report = build_json_report(result)

    errored_payload = report["cases"][1]
    assert errored_payload["status"] == "errored"
    assert errored_payload["error"] is not None
    assert "boom" in errored_payload["error"]
    assert errored_payload["retrieval_metrics"] is None
    assert errored_payload["ticket_metrics"] is None
    assert errored_payload["query_result"] is None


def test_build_json_report_command_args_serialized_as_list() -> None:
    meta = EvalRunMeta(
        schema_version=SCHEMA_VERSION,
        run_started_at="2026-05-10T16:39:04Z",
        run_finished_at="2026-05-10T16:39:42Z",
        llm_used=False,
        retrieval_backend="local_vector_graph_index",
        dataset="mock-v1",
        dataset_path="evaluation/datasets/mock-v1.json",
        dataset_hash="deadbeef" * 8,
        command_args=("run", "--dataset", "x.json"),
    )

    report = build_json_report(_make_result(meta=meta))

    assert report["meta"]["command_args"] == ["run", "--dataset", "x.json"]
    assert isinstance(report["meta"]["command_args"], list)


def test_build_json_report_actual_sources_preserves_order_and_score() -> None:
    case = _make_passed_case()
    # _make_passed_case fixes actual_sources to a 2-element tuple; assert it
    # round-trips into a list with the same order and dict shape.
    result = _make_result(cases=(case,))

    report = build_json_report(result)

    sources = report["cases"][0]["actual_sources"]
    assert isinstance(sources, list)
    assert sources == [
        {"path": "ticket/mock-pol-1001.md", "score": 0.92},
        {"path": "wiki/mock-wiki-5001.md", "score": 0.81},
    ]


def test_dump_json_report_emits_valid_utf8_json() -> None:
    case = _make_passed_case(query="Police MOCK-POL-1001: Bestanden — Routing geprüft.")
    result = _make_result(cases=(case,))

    raw = dump_json_report(result)

    # Round-trips
    parsed = json.loads(raw)
    assert parsed["cases"][0]["query"] == case.query

    # Not escaped to \u sequences (ensure_ascii=False)
    assert "Bestanden" in raw
    assert "geprüft" in raw
    assert "\\u00fc" not in raw  # ü is not escaped
    assert "\\u00df" not in raw  # ß would not appear, but the principle holds


def test_build_json_report_case_count_aggregated_excludes_skipped_and_errored() -> None:
    summary = _make_summary(
        case_count_total=5,
        case_count_aggregated=3,
        passed_count=2,
        failed_count=1,
        skipped_count=1,
        errored_count=1,
        llm_used=False,
    )
    result = _make_result(summary=summary)

    report = build_json_report(result)

    assert report["summary"]["case_count_total"] == 5
    assert report["summary"]["case_count_aggregated"] == 3
    assert report["summary"]["passed_count"] == 2
    assert report["summary"]["failed_count"] == 1
    assert report["summary"]["skipped_count"] == 1
    assert report["summary"]["errored_count"] == 1


# ---------------------------------------------------------------------------
# Additional shape guarantees (not in plan, but tighten the contract)
# ---------------------------------------------------------------------------


def test_build_json_report_top_level_key_order_is_locked() -> None:
    """Top-level dict must list schema_version, meta, summary, cases in that order."""

    report = build_json_report(_make_result())

    assert list(report.keys()) == ["schema_version", "meta", "summary", "cases"]


def test_build_json_report_dump_uses_indent_two_by_default() -> None:
    raw = dump_json_report(_make_result())

    # Default indent=2 → contains "\n  "
    assert "\n  " in raw


def test_build_json_report_dump_allows_compact_output() -> None:
    raw = dump_json_report(_make_result(), indent=None)

    # Compact output → no newlines
    assert "\n" not in raw
    # And still valid JSON
    parsed = json.loads(raw)
    assert parsed["schema_version"] == 1
