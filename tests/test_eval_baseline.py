from __future__ import annotations

import json
from pathlib import Path

import pytest

from ood.eval_baseline import (
    PROPOSED_FIX_TYPES,
    apply_review_decision,
    build_observational_baseline,
    build_review_artifact,
    can_update_baseline,
    save_observational_baseline,
    save_review_artifact,
)


def _report_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "meta": {
            "schema_version": 1,
            "llm_used": False,
            "dataset": "mock-v1",
            "dataset_path": "evaluation/datasets/mock-v1.json",
            "dataset_hash": "deadbeef" * 8,
        },
        "summary": {
            "failed_count": 0,
            "errored_count": 0,
            "llm_used": False,
            "retrieval": {},
            "ticket_intelligence": {},
        },
        "cases": [
            {
                "case_id": "case-1",
                "status": "passed",
                "expected_sources": [],
                "actual_sources": [],
                "retrieval_metrics": None,
                "ticket_metrics": None,
                "query_result": None,
            }
        ],
    }


def _mixed_status_report_payload() -> dict[str, object]:
    report = _report_payload()
    report["summary"] = {
        "failed_count": 1,
        "errored_count": 1,
        "llm_used": False,
        "retrieval": {"Hit@5": 0.5},
        "ticket_intelligence": {"routing_accuracy": 0.5},
    }
    report["cases"] = [
        {
            "case_id": "passed-case",
            "query": "Bestehender Erfolg",
            "status": "passed",
            "expected_sources": ["wiki/success.md"],
            "actual_sources": [{"path": "wiki/success.md", "score": 0.9}],
            "forbidden_sources": [],
            "retrieval_metrics": {"Hit@5": True},
            "ticket_metrics": {"routing_match": True},
            "query_result": {"answer": "ok"},
            "error": None,
            "llm_used": False,
        },
        {
            "case_id": "failed-case",
            "query": "TraceId Kafka nicht gefunden",
            "status": "failed",
            "expected_sources": ["wiki/traceid.md"],
            "actual_sources": [{"path": "wiki/noise.md", "score": 0.7}],
            "forbidden_sources": ["wiki/noise.md"],
            "retrieval_metrics": {"Hit@5": False, "source_recall": 0.0},
            "ticket_metrics": {"routing_match": False},
            "query_result": {"answer": "falsche Quelle"},
            "error": None,
            "llm_used": False,
        },
        {
            "case_id": "skipped-case",
            "query": "LLM benötigt",
            "status": "skipped",
            "expected_sources": [],
            "actual_sources": [],
            "forbidden_sources": [],
            "retrieval_metrics": None,
            "ticket_metrics": None,
            "query_result": None,
            "error": None,
            "llm_used": False,
        },
        {
            "case_id": "errored-case",
            "query": "Engine boom",
            "status": "errored",
            "expected_sources": ["wiki/error.md"],
            "actual_sources": [],
            "forbidden_sources": [],
            "retrieval_metrics": None,
            "ticket_metrics": None,
            "query_result": None,
            "error": "RuntimeError: boom",
            "llm_used": False,
        },
    ]
    return report


def test_build_observational_baseline_wraps_schema_version_1_report_without_thresholds() -> None:
    report = _report_payload()

    baseline = build_observational_baseline(
        report,
        created_at="2026-05-11T10:00:00Z",
        source_report_path=Path("data/evaluation/reports/run.json"),
    )

    assert baseline["schema_version"] == 1
    assert baseline["artifact_type"] == "ood_eval_baseline"
    assert baseline["baseline_version"] == 1
    assert baseline["baseline_kind"] == "observational"
    assert baseline["gate_mode"] == "review_required"
    assert baseline["thresholds"] is None
    assert baseline["created_at"] == "2026-05-11T10:00:00Z"
    assert baseline["source_report_path"] == "data/evaluation/reports/run.json"
    assert isinstance(baseline["source_report_hash"], str)
    assert len(baseline["source_report_hash"]) == 64
    assert baseline["report"] == report


def test_save_observational_baseline_reads_report_and_writes_utf8_indented_json(tmp_path: Path) -> None:
    report_path = tmp_path / "reports" / "eval.json"
    baseline_path = tmp_path / "baselines" / "current.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(json.dumps(_report_payload(), ensure_ascii=False), encoding="utf-8")

    baseline = save_observational_baseline(
        report_path,
        baseline_path,
        created_at="2026-05-11T10:00:00Z",
    )

    assert baseline_path.exists()
    raw = baseline_path.read_text(encoding="utf-8")
    assert "\n  " in raw
    assert json.loads(raw) == baseline
    assert baseline["source_report_path"] == str(report_path)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"schema_version": 2, "meta": {}, "summary": {}, "cases": []},
        {"schema_version": 1, "summary": {}, "cases": []},
        {"schema_version": 1, "meta": {}, "cases": []},
        {"schema_version": 1, "meta": {}, "summary": {}},
        {"schema_version": 1, "meta": [], "summary": {}, "cases": []},
        {"schema_version": 1, "meta": {}, "summary": [], "cases": []},
        {"schema_version": 1, "meta": {}, "summary": {}, "cases": {}},
    ],
)
def test_build_observational_baseline_rejects_invalid_reports(payload: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="schema_version=1 eval report"):
        build_observational_baseline(payload)


def test_observational_baseline_does_not_emit_hard_gate_keys() -> None:
    baseline = build_observational_baseline(_report_payload())
    serialized = json.dumps(baseline, ensure_ascii=False)

    assert baseline["thresholds"] is None
    assert "minimum_hit_at_5" not in serialized
    assert "fail_below" not in serialized
    assert "required_score" not in serialized


def test_build_review_artifact_includes_only_failed_and_errored_cases_with_evidence() -> None:
    review = build_review_artifact(
        _mixed_status_report_payload(),
        created_at="2026-05-11T10:00:00Z",
        source_report_path=Path("data/evaluation/reports/run.json"),
    )

    assert review["schema_version"] == 1
    assert review["artifact_type"] == "ood_eval_review"
    assert review["review_version"] == 1
    assert review["created_at"] == "2026-05-11T10:00:00Z"
    assert review["source_report_path"] == "data/evaluation/reports/run.json"
    assert isinstance(review["source_report_hash"], str)
    assert len(review["source_report_hash"]) == 64
    assert review["report_meta"] == _mixed_status_report_payload()["meta"]
    assert review["report_summary"] == _mixed_status_report_payload()["summary"]
    assert review["decision"] == "deferred"
    assert review["reviewer"] is None
    assert review["rationale"] is None
    assert review["reviewed_at"] is None
    assert review["baseline_update_status"] == "not_requested"
    assert [case["case_id"] for case in review["cases"]] == ["failed-case", "errored-case"]

    failed_case = review["cases"][0]
    assert set(failed_case.keys()) == {
        "case_id",
        "status",
        "query",
        "expected_sources",
        "actual_sources",
        "forbidden_sources",
        "retrieval_metrics",
        "ticket_metrics",
        "evidence",
        "proposed_next_action",
        "proposed_fix_type",
        "proposed_fix_notes",
        "decision",
        "reviewer",
        "rationale",
        "reviewed_at",
        "baseline_update_status",
    }
    assert failed_case["expected_sources"] == ["wiki/traceid.md"]
    assert failed_case["actual_sources"] == [{"path": "wiki/noise.md", "score": 0.7}]
    assert failed_case["forbidden_sources"] == ["wiki/noise.md"]
    assert failed_case["retrieval_metrics"] == {"Hit@5": False, "source_recall": 0.0}
    assert failed_case["ticket_metrics"] == {"routing_match": False}
    assert failed_case["evidence"] == {
        "query_result": {"answer": "falsche Quelle"},
        "error": None,
        "llm_used": False,
    }
    assert failed_case["proposed_next_action"] == "investigate"
    assert failed_case["proposed_fix_type"] == "investigate"
    assert failed_case["proposed_fix_notes"] is None
    assert failed_case["decision"] == "deferred"
    assert failed_case["baseline_update_status"] == "not_requested"


def test_proposed_fix_types_exports_machine_readable_vocabulary() -> None:
    assert PROPOSED_FIX_TYPES == {
        "corpus_fix",
        "retrieval_fix",
        "query_fix",
        "dataset_fix",
        "baseline_update",
        "investigate",
    }


def test_apply_review_decision_updates_top_level_and_deferred_cases_without_overwriting_fix_fields() -> None:
    review = build_review_artifact(_mixed_status_report_payload())
    review["cases"][0]["proposed_fix_type"] = "corpus_fix"
    review["cases"][0]["proposed_fix_notes"] = "Add TraceId synonym metadata."

    decided = apply_review_decision(
        review,
        decision="approved",
        reviewer="Timo",
        rationale="accepted",
        baseline_update_status="requested",
        reviewed_at="2026-05-11T10:05:00Z",
    )

    assert decided["decision"] == "approved"
    assert decided["reviewer"] == "Timo"
    assert decided["rationale"] == "accepted"
    assert decided["reviewed_at"] == "2026-05-11T10:05:00Z"
    assert decided["baseline_update_status"] == "requested"
    for case in decided["cases"]:
        assert case["decision"] == "approved"
        assert case["reviewer"] == "Timo"
        assert case["rationale"] == "accepted"
        assert case["reviewed_at"] == "2026-05-11T10:05:00Z"
        assert case["baseline_update_status"] == "requested"
    assert decided["cases"][0]["proposed_fix_type"] == "corpus_fix"
    assert decided["cases"][0]["proposed_fix_notes"] == "Add TraceId synonym metadata."


def test_apply_review_decision_rejects_unknown_decision_and_status() -> None:
    review = build_review_artifact(_mixed_status_report_payload())

    with pytest.raises(ValueError, match="decision"):
        apply_review_decision(review, decision="maybe")

    with pytest.raises(ValueError, match="baseline_update_status"):
        apply_review_decision(review, decision="approved", baseline_update_status="maybe")


def test_can_update_baseline_requires_approved_review_and_requested_or_approved_update() -> None:
    review = build_review_artifact(_mixed_status_report_payload())

    assert can_update_baseline(review) is False
    assert can_update_baseline({**review, "decision": "approved", "baseline_update_status": "requested"}) is False
    assert can_update_baseline({**review, "decision": "approved", "reviewer": "Timo", "baseline_update_status": "not_requested"}) is False
    assert can_update_baseline({**review, "decision": "rejected", "reviewer": "Timo", "baseline_update_status": "requested"}) is False
    assert can_update_baseline({**review, "decision": "deferred", "reviewer": "Timo", "baseline_update_status": "requested"}) is False
    assert can_update_baseline({**review, "decision": "approved", "reviewer": "Timo", "baseline_update_status": "requested"}) is True
    assert can_update_baseline({**review, "decision": "approved", "reviewer": "Timo", "baseline_update_status": "approved"}) is True


def test_save_review_artifact_reads_report_and_writes_failed_case_review(tmp_path: Path) -> None:
    report_path = tmp_path / "reports" / "eval.json"
    review_path = tmp_path / "reviews" / "run.review.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text(json.dumps(_mixed_status_report_payload(), ensure_ascii=False), encoding="utf-8")

    review = save_review_artifact(
        report_path,
        review_path,
        created_at="2026-05-11T10:00:00Z",
    )

    assert review_path.exists()
    assert json.loads(review_path.read_text(encoding="utf-8")) == review
    assert review["source_report_path"] == str(report_path)
    assert [case["status"] for case in review["cases"]] == ["failed", "errored"]
