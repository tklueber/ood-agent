"""JSON report serializer for the eval runner (Phase 13 Plan 02).

This module is the single source of truth for the wire schema produced by
`EvalRunner.run(...)`. Both stdout JSON output and the `--out` file flag in
Plan 03 import from here — there is exactly ONE schema (D-05, no
`--json` vs `--json-full` split).

Schema invariants:
- Top-level keys, in order: ``schema_version``, ``meta``, ``summary``, ``cases``.
- ``schema_version == 1`` at the top level and inside ``meta``.
- ``meta.llm_used``, ``summary.llm_used``, and per-case ``cases[i].llm_used``
  are always present (D-07).
- Skipped cases keep their slot in ``cases`` with ``status="skipped"`` and
  ``retrieval_metrics``/``ticket_metrics``/``query_result`` set to ``null``
  (D-08); aggregation exclusion is the runner's responsibility.
- Errored cases keep their slot with ``status="errored"`` and a stacktrace
  snippet in ``error`` (D-10).
- Metric dict keys (``Hit@1``, ``mrr``, ``intent_accuracy``, ...) come
  straight from the existing ``*.to_dict()`` shapes and are never renamed.
- German user-facing strings are NOT introduced here — this builder is
  data-only. Plan 03 owns the human formatter (D-04).
"""

from __future__ import annotations

import json
from typing import Any

from ood.eval_runner import EvalCaseResult, EvalRunResult, SCHEMA_VERSION


def build_json_report(result: EvalRunResult) -> dict[str, Any]:
    """Serialize an :class:`EvalRunResult` into the locked wire schema (D-05).

    Returns a plain ``dict`` so callers can post-process the payload (e.g.
    inject CI metadata) before serialization. The top-level key order is
    locked to ``schema_version``, ``meta``, ``summary``, ``cases``.
    """

    return {
        "schema_version": SCHEMA_VERSION,
        "meta": _build_meta(result),
        "summary": _build_summary(result),
        "cases": [_build_case(case) for case in result.cases],
    }


def dump_json_report(result: EvalRunResult, *, indent: int | None = 2) -> str:
    """Serialize the report to a UTF-8 JSON string.

    Used by both stdout output and ``--out`` file writes in Plan 03.
    Always uses ``ensure_ascii=False`` so German strings round-trip
    verbatim (``Bestanden`` stays ``Bestanden``, not ``\\u00...``).
    """

    return json.dumps(
        build_json_report(result),
        ensure_ascii=False,
        indent=indent,
        sort_keys=False,
    )


def _build_meta(result: EvalRunResult) -> dict[str, Any]:
    meta = result.meta
    return {
        "schema_version": meta.schema_version,
        "run_started_at": meta.run_started_at,
        "run_finished_at": meta.run_finished_at,
        "llm_used": meta.llm_used,
        "retrieval_backend": meta.retrieval_backend,
        "dataset": meta.dataset,
        "dataset_path": meta.dataset_path,
        "dataset_hash": meta.dataset_hash,
        "command_args": list(meta.command_args),
    }


def _build_summary(result: EvalRunResult) -> dict[str, Any]:
    summary = result.summary
    return {
        "case_count_total": summary.case_count_total,
        "case_count_aggregated": summary.case_count_aggregated,
        "passed_count": summary.passed_count,
        "failed_count": summary.failed_count,
        "skipped_count": summary.skipped_count,
        "errored_count": summary.errored_count,
        "llm_used": summary.llm_used,
        "retrieval": dict(summary.retrieval),
        "ticket_intelligence": dict(summary.ticket_intelligence),
    }


def _build_case(case: EvalCaseResult) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "query": case.query,
        "status": case.status,
        "skip_reason": case.skip_reason,
        "error": case.error,
        "llm_used": case.llm_used,
        "expected_sources": list(case.expected_sources),
        "forbidden_sources": list(case.forbidden_sources),
        "actual_sources": [dict(source) for source in case.actual_sources],
        "expected_llm_answer": case.expected_llm_answer,
        "retrieval_metrics": case.retrieval_metrics,
        "ticket_metrics": case.ticket_metrics,
        "query_result": case.query_result,
    }


__all__ = ["build_json_report", "dump_json_report"]
