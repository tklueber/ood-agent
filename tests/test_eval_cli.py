"""Tests for the ``ood eval`` Typer sub-app (Phase 13 Plan 03).

The eval CLI wires ``EvalRunner`` (Plan 01) and the JSON serializer (Plan 02)
behind the ``eval`` namespace, renders German human output, and enforces
the exit-code policy (0 on successful run, 1 on hard errors). These tests
exercise help text, flag parsing, German strings, the LLM marker, exit
codes, file output, and reverse-direction import safety.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from ood import eval_cli
from ood.cli import app
from ood.eval_runner import (
    EvalCaseResult,
    EvalRunMeta,
    EvalRunResult,
    EvalRunSummary,
    EvalRunner,
    EvalRunnerError,
    SCHEMA_VERSION,
)
from ood.eval_report import dump_json_report
from ood.models import IndexMissingError


runner = CliRunner()


# ---------------------------------------------------------------------------
# Dataset fixtures
# ---------------------------------------------------------------------------


def _write_minimal_dataset(path: Path, *, dataset_name: str = "mock-v1") -> Path:
    payload = {
        "schema_version": 1,
        "dataset": dataset_name,
        "cases": [
            {
                "id": "case-1",
                "query": "Police MOCK-POL-1001 bricht beim Login ab.",
                "expected_sources": ["ticket/mock-pol-1001.md"],
                "forbidden_sources": [],
                "expected_intent": "Problem",
                "expected_route": "weiterleiten Policen",
                "expected_identifiers": [
                    {"kind": "police", "value": "MOCK-POL-1001"}
                ],
                "expected_command_risks": [],
                "expected_uncertainties": [],
            }
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _make_knowledge_dir(tmp_path: Path, *, source_paths: tuple[str, ...] = ("ticket/mock-pol-1001.md", "ticket/mock-pol-1003.md", "wiki/mock-wiki-5003.md", "note/mock-note-7003.md", "ticket/mock-pol-2002.md", "ticket/mock-pol-3003.md")) -> Path:
    """Create a tmp knowledge dir with stub Markdown files for each path."""

    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir(exist_ok=True)
    for source in source_paths:
        target = knowledge_dir / source
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(f"# {source}\nStub", encoding="utf-8")
    return knowledge_dir


def _write_multi_case_dataset(path: Path, case_ids: list[str]) -> Path:
    payload = {
        "schema_version": 1,
        "dataset": "mock-v1",
        "cases": [
            {
                "id": case_id,
                "query": f"Query for {case_id}",
                "expected_sources": ["ticket/mock-pol-1001.md"],
                "forbidden_sources": [],
                "expected_intent": "Problem",
                "expected_route": "weiterleiten Policen",
                "expected_identifiers": [],
                "expected_command_risks": [],
                "expected_uncertainties": [],
            }
            for case_id in case_ids
        ],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# EvalRunResult fixture builder
# ---------------------------------------------------------------------------


def _make_meta(*, llm_used: bool = False, dataset_path: str = "evaluation/datasets/mock-v1.json") -> EvalRunMeta:
    return EvalRunMeta(
        schema_version=SCHEMA_VERSION,
        run_started_at="2026-05-10T16:39:04Z",
        run_finished_at="2026-05-10T16:39:42Z",
        llm_used=llm_used,
        retrieval_backend="local_vector_graph_index",
        dataset="mock-v1",
        dataset_path=dataset_path,
        dataset_hash="deadbeef" * 8,
        command_args=("eval", "run"),
    )


def _make_summary(
    *,
    case_count_total: int = 1,
    passed_count: int = 1,
    failed_count: int = 0,
    skipped_count: int = 0,
    errored_count: int = 0,
    llm_used: bool = False,
) -> EvalRunSummary:
    case_count_aggregated = passed_count + failed_count
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
            "answer": "Antwort",
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
        expected_sources=("ticket/mock-pol-1001.md",),
        forbidden_sources=(),
        actual_sources=({"path": "ticket/mock-pol-1001.md", "score": 0.92},),
        expected_llm_answer=None,
    )


def _make_failed_case(*, case_id: str = "case-fail") -> EvalCaseResult:
    return EvalCaseResult(
        case_id=case_id,
        query="Police MOCK-POL-1003 …",
        status="failed",
        skip_reason=None,
        error=None,
        llm_used=False,
        query_result={
            "query": "Police MOCK-POL-1003 …",
            "sources": [
                {"path": "wiki/mock-wiki-5003.md", "score": 0.71},
                {"path": "note/mock-note-7003.md", "score": 0.55},
            ],
            "llm_used": False,
            "status": "answered",
            "analysis": {"intent": "Unklar"},
            "retrieval_diagnostics": {"backend": "local_vector_graph_index"},
        },
        retrieval_metrics={
            "case_id": case_id,
            "Hit@1": False,
            "Hit@3": True,
            "Hit@5": True,
            "mrr": 0.5,
            "source_recall": 0.5,
            "forbidden_hit": False,
            "forbidden_hit_paths": [],
            "first_relevant_rank": 2,
        },
        ticket_metrics={
            "case_id": case_id,
            "intent_match": False,
            "routing_match": True,
            "identifier_recall": 1.0,
            "command_risk_accuracy": 1.0,
            "uncertainty_match": True,
            "missing_identifiers": [],
            "missing_command_risks": [],
            "missing_uncertainties": [],
        },
        expected_sources=("ticket/mock-pol-1003.md", "wiki/mock-wiki-5003.md"),
        forbidden_sources=(),
        actual_sources=(
            {"path": "wiki/mock-wiki-5003.md", "score": 0.71},
            {"path": "note/mock-note-7003.md", "score": 0.55},
        ),
        expected_llm_answer=None,
    )


def _make_skipped_case(*, case_id: str = "case-skip") -> EvalCaseResult:
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


def _make_errored_case(*, case_id: str = "case-error") -> EvalCaseResult:
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
    passed: int = 0,
    failed: int = 0,
    skipped: int = 0,
    errored: int = 0,
    llm_used: bool = False,
    dataset_path: str = "evaluation/datasets/mock-v1.json",
) -> EvalRunResult:
    cases: list[EvalCaseResult] = []
    for index in range(passed):
        cases.append(_make_passed_case(case_id=f"case-pass-{index}", llm_used=llm_used))
    for index in range(failed):
        cases.append(_make_failed_case(case_id=f"case-fail-{index}"))
    for index in range(skipped):
        cases.append(_make_skipped_case(case_id=f"case-skip-{index}"))
    for index in range(errored):
        cases.append(_make_errored_case(case_id=f"case-error-{index}"))

    meta = _make_meta(llm_used=llm_used, dataset_path=dataset_path)
    summary = _make_summary(
        case_count_total=len(cases),
        passed_count=passed,
        failed_count=failed,
        skipped_count=skipped,
        errored_count=errored,
        llm_used=llm_used,
    )
    return EvalRunResult(meta=meta, summary=summary, cases=tuple(cases))


def _patch_runner(monkeypatch, result: EvalRunResult, *, capture: dict[str, Any] | None = None):
    """Patch EvalRunner.run to return ``result`` and optionally capture kwargs."""

    def fake_run(self, dataset, *, dataset_path, case_id=None, command_args=None):
        if capture is not None:
            capture["dataset"] = dataset
            capture["dataset_path"] = dataset_path
            capture["case_id"] = case_id
            capture["command_args"] = command_args
        return result

    monkeypatch.setattr(EvalRunner, "run", fake_run)


# ---------------------------------------------------------------------------
# Help and discoverability
# ---------------------------------------------------------------------------


def test_eval_help_shows_run_and_cases() -> None:
    result = runner.invoke(app, ["eval", "--help"])

    assert result.exit_code == 0
    assert "run" in result.stdout
    assert "cases" in result.stdout


def test_eval_run_help_lists_documented_flags() -> None:
    result = runner.invoke(app, ["eval", "run", "--help"])

    assert result.exit_code == 0
    assert "--dataset" in result.stdout
    assert "--case-id" in result.stdout
    assert "--out" in result.stdout
    assert "--json" in result.stdout


def test_eval_baseline_help_lists_documented_flags() -> None:
    result = runner.invoke(app, ["eval", "baseline", "--help"])

    assert result.exit_code == 0
    assert "--report" in result.stdout
    assert "--out" in result.stdout
    assert "--json" in result.stdout


def test_eval_baseline_writes_observational_snapshot(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(dump_json_report(_make_result(passed=1), indent=2), encoding="utf-8")
    baseline_path = tmp_path / "baseline.json"

    result = runner.invoke(
        app,
        [
            "eval",
            "baseline",
            "--report",
            str(report_path),
            "--out",
            str(baseline_path),
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert "Baseline gespeichert:" in result.stdout
    assert str(baseline_path) in result.stdout
    payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "ood_eval_baseline"
    assert payload["baseline_kind"] == "observational"
    assert payload["thresholds"] is None
    assert payload["report"]["schema_version"] == 1


def test_eval_baseline_json_emits_compact_summary(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(dump_json_report(_make_result(passed=1), indent=2), encoding="utf-8")
    baseline_path = tmp_path / "baseline.json"

    result = runner.invoke(
        app,
        [
            "eval",
            "baseline",
            "--report",
            str(report_path),
            "--out",
            str(baseline_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert "\n" not in result.stdout.strip()
    payload = json.loads(result.stdout)
    assert payload == {
        "artifact_type": "ood_eval_baseline",
        "baseline_path": str(baseline_path),
        "source_report_hash": payload["source_report_hash"],
        "baseline_kind": "observational",
        "gate_mode": "review_required",
        "thresholds": None,
    }
    assert payload["source_report_hash"]


def test_eval_baseline_default_path_lives_under_ignored_data(
    tmp_path: Path, monkeypatch
) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(dump_json_report(_make_result(passed=1), indent=2), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["eval", "baseline", "--report", str(report_path), "--quiet"],
    )

    assert result.exit_code == 0, result.stderr
    assert (tmp_path / "data" / "evaluation" / "baselines" / "current.json").exists()


def test_eval_baseline_invalid_report_exits_1(tmp_path: Path) -> None:
    bad_report = tmp_path / "bad-report.json"
    bad_report.write_text(json.dumps({"schema_version": 99}), encoding="utf-8")

    result = runner.invoke(app, ["eval", "baseline", "--report", str(bad_report)])

    assert result.exit_code == 1
    combined = (result.stderr or "") + (result.stdout or "")
    assert "Baseline konnte nicht erstellt werden" in combined


def test_eval_review_help_lists_documented_flags() -> None:
    result = runner.invoke(app, ["eval", "review", "--help"])

    assert result.exit_code == 0
    assert "--report" in result.stdout
    assert "--out" in result.stdout
    assert "--json" in result.stdout


def test_eval_review_writes_failed_and_errored_cases_only(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(
        dump_json_report(_make_result(passed=1, failed=1, errored=1), indent=2),
        encoding="utf-8",
    )
    review_path = tmp_path / "review.json"

    result = runner.invoke(
        app,
        [
            "eval",
            "review",
            "--report",
            str(report_path),
            "--out",
            str(review_path),
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert "Review gespeichert:" in result.stdout
    assert "Review-Fälle: 2" in result.stdout
    payload = json.loads(review_path.read_text(encoding="utf-8"))
    assert payload["artifact_type"] == "ood_eval_review"
    assert payload["decision"] == "deferred"
    assert [case["status"] for case in payload["cases"]] == ["failed", "errored"]
    for case in payload["cases"]:
        assert case["proposed_fix_type"] == "investigate"
        assert case["proposed_fix_notes"] is None


def test_eval_review_default_path_uses_dataset_and_hash(
    tmp_path: Path, monkeypatch
) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(dump_json_report(_make_result(failed=1), indent=2), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["eval", "review", "--report", str(report_path), "--quiet"],
    )

    assert result.exit_code == 0, result.stderr
    review_dir = tmp_path / "data" / "evaluation" / "reviews"
    review_files = list(review_dir.glob("mock-v1-deadbeef*.review.json"))
    assert len(review_files) == 1


def test_eval_review_json_emits_summary_and_allowed_fix_types(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(dump_json_report(_make_result(failed=1, errored=1), indent=2), encoding="utf-8")
    review_path = tmp_path / "review.json"

    result = runner.invoke(
        app,
        [
            "eval",
            "review",
            "--report",
            str(report_path),
            "--out",
            str(review_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert "\n" not in result.stdout.strip()
    payload = json.loads(result.stdout)
    assert payload == {
        "artifact_type": "ood_eval_review",
        "review_path": str(review_path),
        "decision": "deferred",
        "baseline_update_status": "not_requested",
        "case_count": 2,
        "proposed_fix_types": [
            "baseline_update",
            "corpus_fix",
            "dataset_fix",
            "investigate",
            "query_fix",
            "retrieval_fix",
        ],
    }


def test_eval_review_invalid_report_exits_1(tmp_path: Path) -> None:
    bad_report = tmp_path / "bad-report.json"
    bad_report.write_text(json.dumps({"schema_version": 99}), encoding="utf-8")

    result = runner.invoke(app, ["eval", "review", "--report", str(bad_report)])

    assert result.exit_code == 1
    combined = (result.stderr or "") + (result.stdout or "")
    assert "Review konnte nicht erstellt werden" in combined


def test_eval_decide_records_approved_review_and_preserves_proposed_fix_metadata(
    tmp_path: Path,
) -> None:
    review_path = tmp_path / "review.json"
    review_path.write_text(
        json.dumps(
            {
                "artifact_type": "ood_eval_review",
                "decision": "deferred",
                "reviewer": None,
                "rationale": None,
                "baseline_update_status": "not_requested",
                "cases": [
                    {
                        "case_id": "case-fail-0",
                        "decision": "deferred",
                        "reviewer": None,
                        "rationale": None,
                        "reviewed_at": None,
                        "baseline_update_status": "not_requested",
                        "proposed_fix_type": "corpus_fix",
                        "proposed_fix_notes": "Add missing wiki note",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "eval",
            "decide",
            "--review",
            str(review_path),
            "--decision",
            "approved",
            "--reviewer",
            "Timo",
            "--rationale",
            "ok",
            "--baseline-update",
            "requested",
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert "Review-Entscheidung gespeichert:" in result.stdout
    payload = json.loads(review_path.read_text(encoding="utf-8"))
    assert payload["decision"] == "approved"
    assert payload["reviewer"] == "Timo"
    assert payload["rationale"] == "ok"
    assert payload["baseline_update_status"] == "requested"
    assert payload["cases"][0]["proposed_fix_type"] == "corpus_fix"
    assert payload["cases"][0]["proposed_fix_notes"] == "Add missing wiki note"


@pytest.mark.parametrize("decision", ["rejected", "deferred"])
def test_eval_decide_records_rejected_and_deferred_decisions(
    tmp_path: Path, decision: str
) -> None:
    review_path = tmp_path / "review.json"
    review_path.write_text(
        json.dumps({"decision": "deferred", "cases": []}, ensure_ascii=False),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "eval",
            "decide",
            "--review",
            str(review_path),
            "--decision",
            decision,
            "--reviewer",
            "Timo",
        ],
    )

    assert result.exit_code == 0, result.stderr
    payload = json.loads(review_path.read_text(encoding="utf-8"))
    assert payload["decision"] == decision
    assert payload["reviewer"] == "Timo"
    assert payload["baseline_update_status"] == "not_requested"


def test_eval_decide_invalid_decision_exits_1(tmp_path: Path) -> None:
    review_path = tmp_path / "review.json"
    review_path.write_text(
        json.dumps({"decision": "deferred", "cases": []}, ensure_ascii=False),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["eval", "decide", "--review", str(review_path), "--decision", "invalid"],
    )

    assert result.exit_code == 1


def test_eval_update_baseline_requires_approved_review_and_preserves_case_fixes(
    tmp_path: Path,
) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(dump_json_report(_make_result(passed=1), indent=2), encoding="utf-8")
    review_path = tmp_path / "review.json"
    review_path.write_text(
        json.dumps(
            {
                "decision": "approved",
                "reviewer": "Timo",
                "baseline_update_status": "requested",
                "cases": [
                    {
                        "case_id": "case-fail-0",
                        "proposed_fix_type": "baseline_update",
                        "proposed_fix_notes": "Accept new observed baseline",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    baseline_path = tmp_path / "baseline.json"

    result = runner.invoke(
        app,
        [
            "eval",
            "update-baseline",
            "--report",
            str(report_path),
            "--review",
            str(review_path),
            "--out",
            str(baseline_path),
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert "Baseline aktualisiert:" in result.stdout
    assert json.loads(baseline_path.read_text(encoding="utf-8"))["artifact_type"] == "ood_eval_baseline"
    review_payload = json.loads(review_path.read_text(encoding="utf-8"))
    assert review_payload["baseline_update_status"] == "updated"
    assert review_payload["cases"][0]["proposed_fix_type"] == "baseline_update"
    assert review_payload["cases"][0]["proposed_fix_notes"] == "Accept new observed baseline"


@pytest.mark.parametrize(
    ("review_payload"),
    [
        {"decision": "rejected", "reviewer": "Timo", "baseline_update_status": "requested"},
        {"decision": "deferred", "reviewer": "Timo", "baseline_update_status": "requested"},
        {"decision": "approved", "reviewer": "", "baseline_update_status": "requested"},
        {"decision": "approved", "reviewer": "Timo", "baseline_update_status": "not_requested"},
    ],
)
def test_eval_update_baseline_blocks_without_explicit_approval(
    tmp_path: Path, review_payload: dict[str, Any]
) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(dump_json_report(_make_result(passed=1), indent=2), encoding="utf-8")
    review_path = tmp_path / "review.json"
    review_path.write_text(json.dumps(review_payload, ensure_ascii=False), encoding="utf-8")
    baseline_path = tmp_path / "baseline.json"

    result = runner.invoke(
        app,
        [
            "eval",
            "update-baseline",
            "--report",
            str(report_path),
            "--review",
            str(review_path),
            "--out",
            str(baseline_path),
        ],
    )

    assert result.exit_code == 1
    combined = (result.stderr or "") + (result.stdout or "")
    assert "Baseline-Update erfordert eine genehmigte Review-Entscheidung." in combined
    assert not baseline_path.exists()


# ---------------------------------------------------------------------------
# Dataset resolution
# ---------------------------------------------------------------------------


def test_eval_run_uses_settings_eval_dataset_path_by_default(
    tmp_path: Path, monkeypatch
) -> None:
    knowledge_dir = _make_knowledge_dir(tmp_path)
    dataset_path = _write_minimal_dataset(tmp_path / "cases.json")
    monkeypatch.setenv("OOD_EVAL_DATASET", str(dataset_path))

    capture: dict[str, Any] = {}
    _patch_runner(monkeypatch, _make_result(passed=1), capture=capture)

    result = runner.invoke(
        app,
        ["eval", "run", "--knowledge-dir", str(knowledge_dir), "--quiet"],
    )

    assert result.exit_code == 0, result.stderr
    assert capture["dataset_path"] == dataset_path.resolve()


def test_eval_run_dataset_flag_overrides_env(tmp_path: Path, monkeypatch) -> None:
    knowledge_dir = _make_knowledge_dir(tmp_path)
    env_dataset = _write_minimal_dataset(tmp_path / "env.json")
    flag_dataset = _write_minimal_dataset(tmp_path / "flag.json")
    monkeypatch.setenv("OOD_EVAL_DATASET", str(env_dataset))

    capture: dict[str, Any] = {}
    _patch_runner(monkeypatch, _make_result(passed=1), capture=capture)

    result = runner.invoke(
        app,
        [
            "eval",
            "run",
            "--knowledge-dir",
            str(knowledge_dir),
            "--dataset",
            str(flag_dataset),
            "--quiet",
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert capture["dataset_path"] == flag_dataset.resolve()


def test_eval_run_missing_dataset_exits_1(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist.json"

    result = runner.invoke(app, ["eval", "run", "--dataset", str(missing)])

    assert result.exit_code == 1
    combined = (result.stderr or "") + (result.stdout or "")
    assert "nicht gefunden" in combined


def test_eval_run_malformed_dataset_exits_1(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"schema_version": 99, "dataset": "x", "cases": []}), encoding="utf-8")

    result = runner.invoke(app, ["eval", "run", "--dataset", str(bad)])

    assert result.exit_code == 1
    combined = (result.stderr or "") + (result.stdout or "")
    assert "Datensatz konnte nicht geladen werden" in combined


# ---------------------------------------------------------------------------
# Human output (German)
# ---------------------------------------------------------------------------


def test_eval_run_renders_german_header_with_llm_used_no(
    tmp_path: Path, monkeypatch
) -> None:
    knowledge_dir = _make_knowledge_dir(tmp_path)
    dataset_path = _write_minimal_dataset(tmp_path / "cases.json")
    _patch_runner(monkeypatch, _make_result(passed=1, llm_used=False))

    result = runner.invoke(
        app,
        [
            "eval",
            "run",
            "--knowledge-dir",
            str(knowledge_dir),
            "--dataset",
            str(dataset_path),
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert "OOD Evaluation" in result.stdout
    assert "Cloud-LLM verwendet: nein" in result.stdout
    assert "Bestanden" in result.stdout
    assert "Fehlgeschlagen" in result.stdout
    assert "Zusammenfassung" in result.stdout


def test_eval_run_renders_llm_marker_when_llm_used_true(
    tmp_path: Path, monkeypatch
) -> None:
    knowledge_dir = _make_knowledge_dir(tmp_path)
    dataset_path = _write_minimal_dataset(tmp_path / "cases.json")
    _patch_runner(monkeypatch, _make_result(passed=1, llm_used=True))

    result = runner.invoke(
        app,
        [
            "eval",
            "run",
            "--knowledge-dir",
            str(knowledge_dir),
            "--dataset",
            str(dataset_path),
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert "»LLM«" in result.stdout
    assert "Cloud-LLM verwendet: ja" in result.stdout


def test_eval_run_human_output_does_not_enumerate_passed_cases(
    tmp_path: Path, monkeypatch
) -> None:
    knowledge_dir = _make_knowledge_dir(tmp_path)
    dataset_path = _write_minimal_dataset(tmp_path / "cases.json")
    _patch_runner(monkeypatch, _make_result(passed=5))

    result = runner.invoke(
        app,
        [
            "eval",
            "run",
            "--knowledge-dir",
            str(knowledge_dir),
            "--dataset",
            str(dataset_path),
        ],
    )

    assert result.exit_code == 0, result.stderr
    for index in range(5):
        assert f"case-pass-{index}" not in result.stdout
    assert "Bestanden" in result.stdout
    # The number 5 appears in the summary somewhere
    assert "5" in result.stdout


def test_eval_run_human_output_lists_failed_cases_with_expected_actual(
    tmp_path: Path, monkeypatch
) -> None:
    knowledge_dir = _make_knowledge_dir(tmp_path)
    dataset_path = _write_minimal_dataset(tmp_path / "cases.json")
    _patch_runner(monkeypatch, _make_result(failed=1))

    result = runner.invoke(
        app,
        [
            "eval",
            "run",
            "--knowledge-dir",
            str(knowledge_dir),
            "--dataset",
            str(dataset_path),
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert "case-fail-0" in result.stdout
    assert "Fehlgeschlagene Fälle" in result.stdout
    # Expected source
    assert "ticket/mock-pol-1003.md" in result.stdout
    # Actual source with score formatted
    assert "wiki/mock-wiki-5003.md" in result.stdout
    assert "0.71" in result.stdout
    # Mismatch line
    assert "Mismatch" in result.stdout
    assert "Hit@1" in result.stdout


def test_eval_run_human_output_lists_skipped_cases_separately(
    tmp_path: Path, monkeypatch
) -> None:
    knowledge_dir = _make_knowledge_dir(tmp_path)
    dataset_path = _write_minimal_dataset(tmp_path / "cases.json")
    _patch_runner(monkeypatch, _make_result(passed=1, skipped=1))

    result = runner.invoke(
        app,
        [
            "eval",
            "run",
            "--knowledge-dir",
            str(knowledge_dir),
            "--dataset",
            str(dataset_path),
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert "Übersprungene Fälle" in result.stdout
    assert "llm_required" in result.stdout
    assert "case-skip-0" in result.stdout
    # Skipped case must NOT appear under "Fehlgeschlagene Fälle"
    failed_section_start = result.stdout.find("Fehlgeschlagene Fälle")
    skipped_section_start = result.stdout.find("Übersprungene Fälle")
    assert failed_section_start != -1
    assert skipped_section_start != -1
    failed_section = result.stdout[failed_section_start:skipped_section_start]
    assert "case-skip-0" not in failed_section


def test_eval_run_human_output_lists_errored_cases_separately(
    tmp_path: Path, monkeypatch
) -> None:
    knowledge_dir = _make_knowledge_dir(tmp_path)
    dataset_path = _write_minimal_dataset(tmp_path / "cases.json")
    _patch_runner(monkeypatch, _make_result(passed=1, errored=1))

    result = runner.invoke(
        app,
        [
            "eval",
            "run",
            "--knowledge-dir",
            str(knowledge_dir),
            "--dataset",
            str(dataset_path),
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert "Fehler:" in result.stdout
    assert "boom" in result.stdout
    assert "case-error-0" in result.stdout
    # Errored case must NOT appear under "Fehlgeschlagene Fälle"
    failed_section_start = result.stdout.find("Fehlgeschlagene Fälle")
    errored_section_start = result.stdout.find("Fehler:")
    assert failed_section_start != -1
    assert errored_section_start != -1
    failed_section = result.stdout[failed_section_start:errored_section_start]
    assert "case-error-0" not in failed_section


# ---------------------------------------------------------------------------
# Exit-code policy (D-09 / D-10)
# ---------------------------------------------------------------------------


def test_eval_run_exit_code_zero_when_failures_present(
    tmp_path: Path, monkeypatch
) -> None:
    knowledge_dir = _make_knowledge_dir(tmp_path)
    dataset_path = _write_minimal_dataset(tmp_path / "cases.json")
    _patch_runner(monkeypatch, _make_result(failed=1))

    result = runner.invoke(
        app,
        [
            "eval",
            "run",
            "--knowledge-dir",
            str(knowledge_dir),
            "--dataset",
            str(dataset_path),
        ],
    )

    assert result.exit_code == 0


def test_eval_run_exit_code_zero_when_errored_present(
    tmp_path: Path, monkeypatch
) -> None:
    knowledge_dir = _make_knowledge_dir(tmp_path)
    dataset_path = _write_minimal_dataset(tmp_path / "cases.json")
    _patch_runner(monkeypatch, _make_result(errored=1))

    result = runner.invoke(
        app,
        [
            "eval",
            "run",
            "--knowledge-dir",
            str(knowledge_dir),
            "--dataset",
            str(dataset_path),
        ],
    )

    assert result.exit_code == 0


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------


def test_eval_run_json_emits_wire_schema_to_stdout(
    tmp_path: Path, monkeypatch
) -> None:
    knowledge_dir = _make_knowledge_dir(tmp_path)
    dataset_path = _write_minimal_dataset(tmp_path / "cases.json")
    _patch_runner(monkeypatch, _make_result(passed=1))

    result = runner.invoke(
        app,
        [
            "eval",
            "run",
            "--knowledge-dir",
            str(knowledge_dir),
            "--dataset",
            str(dataset_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == 1
    assert payload["meta"]["llm_used"] in (True, False)
    assert "summary" in payload
    assert "cases" in payload


def test_eval_run_out_writes_indented_json_to_file(
    tmp_path: Path, monkeypatch
) -> None:
    knowledge_dir = _make_knowledge_dir(tmp_path)
    dataset_path = _write_minimal_dataset(tmp_path / "cases.json")
    _patch_runner(monkeypatch, _make_result(passed=1))

    out_path = tmp_path / "report.json"
    result = runner.invoke(
        app,
        [
            "eval",
            "run",
            "--knowledge-dir",
            str(knowledge_dir),
            "--dataset",
            str(dataset_path),
            "--json",
            "--out",
            str(out_path),
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert out_path.exists()
    file_text = out_path.read_text(encoding="utf-8")
    assert "\n" in file_text  # indent=2 produces newlines
    parsed = json.loads(file_text)
    assert parsed["schema_version"] == 1
    # stdout compact JSON also written
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == 1


def test_eval_run_out_creates_parent_directories(
    tmp_path: Path, monkeypatch
) -> None:
    knowledge_dir = _make_knowledge_dir(tmp_path)
    dataset_path = _write_minimal_dataset(tmp_path / "cases.json")
    _patch_runner(monkeypatch, _make_result(passed=1))

    out_path = tmp_path / "nested" / "dir" / "report.json"
    result = runner.invoke(
        app,
        [
            "eval",
            "run",
            "--knowledge-dir",
            str(knowledge_dir),
            "--dataset",
            str(dataset_path),
            "--out",
            str(out_path),
            "--quiet",
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert out_path.exists()
    parsed = json.loads(out_path.read_text(encoding="utf-8"))
    assert parsed["schema_version"] == 1


# ---------------------------------------------------------------------------
# Error paths (hard errors)
# ---------------------------------------------------------------------------


def test_eval_run_unknown_case_id_exits_1(tmp_path: Path, monkeypatch) -> None:
    knowledge_dir = _make_knowledge_dir(tmp_path)
    dataset_path = _write_minimal_dataset(tmp_path / "cases.json")

    def fake_run(self, dataset, *, dataset_path, case_id=None, command_args=None):
        raise EvalRunnerError("Unknown case_id: 'missing'")

    monkeypatch.setattr(EvalRunner, "run", fake_run)

    result = runner.invoke(
        app,
        [
            "eval",
            "run",
            "--knowledge-dir",
            str(knowledge_dir),
            "--dataset",
            str(dataset_path),
            "--case-id",
            "missing",
        ],
    )

    assert result.exit_code == 1
    combined = (result.stderr or "") + (result.stdout or "")
    assert "Unknown case_id" in combined


def test_eval_run_index_missing_exits_1(tmp_path: Path, monkeypatch) -> None:
    knowledge_dir = _make_knowledge_dir(tmp_path)
    dataset_path = _write_minimal_dataset(tmp_path / "cases.json")

    def fake_run(self, dataset, *, dataset_path, case_id=None, command_args=None):
        raise IndexMissingError("No index found. Run `ood index` first.")

    monkeypatch.setattr(EvalRunner, "run", fake_run)

    result = runner.invoke(
        app,
        [
            "eval",
            "run",
            "--knowledge-dir",
            str(knowledge_dir),
            "--dataset",
            str(dataset_path),
        ],
    )

    assert result.exit_code == 1
    combined = (result.stderr or "") + (result.stdout or "")
    assert "Kein Index gefunden" in combined
    assert "ood index" in combined


def test_eval_run_exit_code_one_when_index_missing(
    tmp_path: Path, monkeypatch
) -> None:
    """BLOCKER 2 follow-through: end-to-end IndexMissingError via RagEngine.query."""

    knowledge_dir = _make_knowledge_dir(tmp_path)
    dataset_path = _write_minimal_dataset(tmp_path / "cases.json")

    from ood import rag as rag_module

    def fake_query(self, query_text):
        raise IndexMissingError("No index found. Run `ood index` first.")

    # Build a no-op RagEngine __init__ so we don't need a real index on disk.
    monkeypatch.setattr(
        rag_module.RagEngine,
        "__init__",
        lambda self, settings: setattr(self, "settings", settings),
    )
    monkeypatch.setattr(rag_module.RagEngine, "query", fake_query)

    result = runner.invoke(
        app,
        [
            "eval",
            "run",
            "--knowledge-dir",
            str(knowledge_dir),
            "--dataset",
            str(dataset_path),
        ],
    )

    assert result.exit_code == 1
    combined = (result.stderr or "") + (result.stdout or "")
    assert "Kein Index gefunden" in combined


# ---------------------------------------------------------------------------
# cases subcommand
# ---------------------------------------------------------------------------


def test_eval_cases_lists_sorted_case_ids_with_query(tmp_path: Path) -> None:
    knowledge_dir = _make_knowledge_dir(tmp_path)
    dataset_path = _write_multi_case_dataset(
        tmp_path / "cases.json", ["c-2", "c-1", "c-3"]
    )

    result = runner.invoke(
        app,
        [
            "eval",
            "cases",
            "--knowledge-dir",
            str(knowledge_dir),
            "--dataset",
            str(dataset_path),
        ],
    )

    assert result.exit_code == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    # Lines should appear sorted by case_id
    indices = [line.split(":")[0] for line in lines if ":" in line]
    assert indices == sorted(indices)
    assert "c-1" in result.stdout
    assert "c-2" in result.stdout
    assert "c-3" in result.stdout
    assert "Query for c-1" in result.stdout


def test_eval_cases_json_emits_dataset_name_and_cases(tmp_path: Path) -> None:
    knowledge_dir = _make_knowledge_dir(tmp_path)
    dataset_path = _write_multi_case_dataset(
        tmp_path / "cases.json", ["c-2", "c-1", "c-3"]
    )

    result = runner.invoke(
        app,
        [
            "eval",
            "cases",
            "--knowledge-dir",
            str(knowledge_dir),
            "--dataset",
            str(dataset_path),
            "--json",
        ],
    )

    assert result.exit_code == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["dataset"] == "mock-v1"
    case_ids = [case["case_id"] for case in payload["cases"]]
    assert case_ids == sorted(case_ids)
    assert set(case_ids) == {"c-1", "c-2", "c-3"}


# ---------------------------------------------------------------------------
# Quiet mode
# ---------------------------------------------------------------------------


def test_eval_cli_quiet_suppresses_human_output(
    tmp_path: Path, monkeypatch
) -> None:
    knowledge_dir = _make_knowledge_dir(tmp_path)
    dataset_path = _write_minimal_dataset(tmp_path / "cases.json")
    _patch_runner(monkeypatch, _make_result(passed=1))

    result = runner.invoke(
        app,
        [
            "eval",
            "run",
            "--knowledge-dir",
            str(knowledge_dir),
            "--dataset",
            str(dataset_path),
            "--quiet",
        ],
    )

    assert result.exit_code == 0, result.stderr
    assert result.stdout == ""


# ---------------------------------------------------------------------------
# Reverse-direction import safety (WARNING 4)
# ---------------------------------------------------------------------------


def test_eval_cli_module_importable_directly() -> None:
    """Ensure ``from ood.eval_cli import eval_app`` works on its own.

    Plan 03 introduces a deferred import in ``ood.cli`` to register the eval
    sub-app. This test guards against a regression in which a fresh process
    that imports ``ood.eval_cli`` before ``ood.cli`` triggers a partial-load
    circular ``ImportError``.
    """

    result = subprocess.run(
        ["uv", "run", "python", "-c", "from ood.eval_cli import eval_app; print('ok')"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert "ok" in result.stdout
