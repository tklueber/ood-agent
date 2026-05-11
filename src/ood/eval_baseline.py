"""Baseline and review artifacts for local evaluation reports.

Phase 14 keeps these helpers pure and stdlib-only so CLI commands can build on
the locked ``schema_version=1`` report payload without introducing threshold
gates or additional evaluation logic.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping


DECISIONS = {"approved", "rejected", "deferred"}
BASELINE_UPDATE_STATUSES = {"not_requested", "requested", "approved", "rejected", "updated"}
PROPOSED_FIX_TYPES = {
    "corpus_fix",
    "retrieval_fix",
    "query_fix",
    "dataset_fix",
    "baseline_update",
    "investigate",
}


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stable_hash(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _validate_eval_report(report: Mapping[str, Any]) -> None:
    if (
        report.get("schema_version") != 1
        or not isinstance(report.get("meta"), dict)
        or not isinstance(report.get("summary"), dict)
        or not isinstance(report.get("cases"), list)
    ):
        raise ValueError("Expected schema_version=1 eval report with meta, summary, and cases")


def _validate_proposed_fix_type(value: str) -> None:
    if value not in PROPOSED_FIX_TYPES:
        raise ValueError(f"Unknown proposed_fix_type: {value}")


def _validate_decision(value: str) -> None:
    if value not in DECISIONS:
        raise ValueError(f"Unknown decision: {value}")


def _validate_baseline_update_status(value: str) -> None:
    if value not in BASELINE_UPDATE_STATUSES:
        raise ValueError(f"Unknown baseline_update_status: {value}")


def load_json_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def write_json_file(payload: Mapping[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False),
        encoding="utf-8",
    )


def build_observational_baseline(
    report: Mapping[str, Any],
    *,
    created_at: str | None = None,
    source_report_path: Path | None = None,
) -> dict[str, Any]:
    _validate_eval_report(report)
    report_payload = dict(report)
    return {
        "schema_version": 1,
        "artifact_type": "ood_eval_baseline",
        "baseline_version": 1,
        "baseline_kind": "observational",
        "gate_mode": "review_required",
        "thresholds": None,
        "created_at": created_at or _utc_now_iso(),
        "source_report_path": str(source_report_path) if source_report_path is not None else None,
        "source_report_hash": _stable_hash(report_payload),
        "report": report_payload,
    }


def save_observational_baseline(
    report_path: Path,
    baseline_path: Path,
    *,
    created_at: str | None = None,
) -> dict[str, Any]:
    report = load_json_file(report_path)
    baseline = build_observational_baseline(
        report,
        created_at=created_at,
        source_report_path=report_path,
    )
    write_json_file(baseline, baseline_path)
    return baseline


def _review_case(case: Mapping[str, Any]) -> dict[str, Any]:
    proposed_fix_type = "investigate"
    _validate_proposed_fix_type(proposed_fix_type)
    return {
        "case_id": case.get("case_id"),
        "status": case.get("status"),
        "query": case.get("query"),
        "expected_sources": list(case.get("expected_sources") or []),
        "actual_sources": [dict(source) for source in case.get("actual_sources") or []],
        "forbidden_sources": list(case.get("forbidden_sources") or []),
        "retrieval_metrics": case.get("retrieval_metrics"),
        "ticket_metrics": case.get("ticket_metrics"),
        "evidence": {
            "query_result": case.get("query_result"),
            "error": case.get("error"),
            "llm_used": case.get("llm_used"),
        },
        "proposed_next_action": "investigate",
        "proposed_fix_type": proposed_fix_type,
        "proposed_fix_notes": None,
        "decision": "deferred",
        "reviewer": None,
        "rationale": None,
        "reviewed_at": None,
        "baseline_update_status": "not_requested",
    }


def build_review_artifact(
    report: Mapping[str, Any],
    *,
    created_at: str | None = None,
    source_report_path: Path | None = None,
) -> dict[str, Any]:
    _validate_eval_report(report)
    report_payload = dict(report)
    return {
        "schema_version": 1,
        "artifact_type": "ood_eval_review",
        "review_version": 1,
        "created_at": created_at or _utc_now_iso(),
        "source_report_path": str(source_report_path) if source_report_path is not None else None,
        "source_report_hash": _stable_hash(report_payload),
        "report_meta": dict(report["meta"]),
        "report_summary": dict(report["summary"]),
        "decision": "deferred",
        "reviewer": None,
        "rationale": None,
        "reviewed_at": None,
        "baseline_update_status": "not_requested",
        "cases": [
            _review_case(case)
            for case in report["cases"]
            if isinstance(case, Mapping) and case.get("status") in {"failed", "errored"}
        ],
    }


def save_review_artifact(
    report_path: Path,
    review_path: Path,
    *,
    created_at: str | None = None,
) -> dict[str, Any]:
    report = load_json_file(report_path)
    review = build_review_artifact(report, created_at=created_at, source_report_path=report_path)
    write_json_file(review, review_path)
    return review


def apply_review_decision(
    review: Mapping[str, Any],
    *,
    decision: str,
    reviewer: str | None = None,
    rationale: str | None = None,
    baseline_update_status: str = "not_requested",
    reviewed_at: str | None = None,
) -> dict[str, Any]:
    _validate_decision(decision)
    _validate_baseline_update_status(baseline_update_status)
    updated = dict(review)
    updated["decision"] = decision
    updated["reviewer"] = reviewer
    updated["rationale"] = rationale
    updated["reviewed_at"] = reviewed_at or _utc_now_iso()
    updated["baseline_update_status"] = baseline_update_status
    updated_cases: list[dict[str, Any]] = []
    for case in review.get("cases") or []:
        if not isinstance(case, Mapping):
            continue
        case_payload = dict(case)
        _validate_proposed_fix_type(str(case_payload.get("proposed_fix_type", "investigate")))
        if case_payload.get("decision") == "deferred":
            case_payload["decision"] = decision
            case_payload["reviewer"] = reviewer
            case_payload["rationale"] = rationale
            case_payload["reviewed_at"] = updated["reviewed_at"]
            case_payload["baseline_update_status"] = baseline_update_status
        updated_cases.append(case_payload)
    updated["cases"] = updated_cases
    return updated


def can_update_baseline(review: Mapping[str, Any]) -> bool:
    return (
        review.get("decision") == "approved"
        and bool(review.get("reviewer"))
        and review.get("baseline_update_status") in {"requested", "approved"}
    )


__all__ = [
    "DECISIONS",
    "BASELINE_UPDATE_STATUSES",
    "PROPOSED_FIX_TYPES",
    "build_observational_baseline",
    "save_observational_baseline",
    "build_review_artifact",
    "save_review_artifact",
    "apply_review_decision",
    "can_update_baseline",
    "load_json_file",
    "write_json_file",
]
