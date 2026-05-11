from __future__ import annotations

import hashlib
import traceback
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ood.config import Settings
from ood.evaluation import EvaluationCase, EvaluationDataset
from ood.evaluation_metrics import (
    RetrievalCaseMetrics,
    evaluate_retrieval_case,
    summarize_retrieval_metrics,
)
from ood.evaluation_ticket_metrics import (
    TicketIntelligenceCaseMetrics,
    evaluate_ticket_intelligence_case,
    summarize_ticket_intelligence_metrics,
)
from ood.models import IndexMissingError, QueryResult
from ood.rag import RagEngine


SCHEMA_VERSION = 1


class EvalRunnerError(RuntimeError):
    """Raised for runner-level configuration errors (e.g. unknown case_id)."""


@dataclass(frozen=True)
class EvalCaseResult:
    """Per-case eval outcome ready for JSON report and CLI rendering."""

    case_id: str
    query: str
    status: str  # "passed" | "failed" | "skipped" | "errored"
    skip_reason: str | None
    error: str | None  # stacktrace snippet for status=="errored"
    llm_used: bool
    query_result: dict[str, Any] | None  # full QueryResult.to_dict() or None
    retrieval_metrics: dict[str, Any] | None
    ticket_metrics: dict[str, Any] | None
    expected_sources: tuple[str, ...]
    forbidden_sources: tuple[str, ...]
    actual_sources: tuple[dict[str, Any], ...]
    expected_llm_answer: str | None


@dataclass(frozen=True)
class EvalRunSummary:
    """Aggregated counts and metric summaries over the executed run."""

    case_count_total: int
    case_count_aggregated: int  # passed + failed only
    passed_count: int
    failed_count: int
    skipped_count: int
    errored_count: int
    llm_used: bool
    retrieval: dict[str, Any]
    ticket_intelligence: dict[str, Any]


@dataclass(frozen=True)
class EvalRunMeta:
    """Run-level metadata (privacy posture, provenance, timing)."""

    schema_version: int
    run_started_at: str
    run_finished_at: str
    llm_used: bool
    retrieval_backend: str
    dataset: str
    dataset_path: str
    dataset_hash: str
    command_args: tuple[str, ...]


@dataclass(frozen=True)
class EvalRunResult:
    """Top-level runner output consumed by Plan 02 (JSON) and Plan 03 (CLI)."""

    meta: EvalRunMeta
    summary: EvalRunSummary
    cases: tuple[EvalCaseResult, ...]


class EvalRunner:
    """Drive EvaluationDataset cases through the public RagEngine.query() contract."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @staticmethod
    def _engine_settings(settings: Settings) -> Settings:
        # DELIBERATE DIVERGENCE from `ood query` (CONTEXT.md D-06):
        # Eval activates the Cloud-LLM path on credential availability alone.
        # RagEngine internally gates LLM usage on the Settings privacy
        # property (which requires both the privacy ENV approval AND
        # credentials), so we forge an effective Settings object in which
        # `allow_cloud_llm` is True whenever credentials exist. This is the
        # ONLY place in eval_runner.py that may reference `allow_cloud_llm`.
        # Business logic elsewhere consults `has_llm_credentials` exclusively.
        if settings.has_llm_credentials:
            return settings.model_copy(update={"allow_cloud_llm": True})
        return settings

    def run(
        self,
        dataset: EvaluationDataset,
        *,
        dataset_path: Path,
        case_id: str | None = None,
        command_args: Sequence[str] | None = None,
    ) -> EvalRunResult:
        started_at = self._utc_now_iso()

        if case_id is not None:
            cases_to_run = tuple(case for case in dataset.cases if case.id == case_id)
            if not cases_to_run:
                msg = f"Unknown case_id: {case_id!r}"
                raise EvalRunnerError(msg)
        else:
            cases_to_run = dataset.cases

        dataset_hash = hashlib.sha256(dataset_path.read_bytes()).hexdigest()

        engine = RagEngine(self._engine_settings(self.settings))

        # D-06 business-logic gate: credential availability only.
        llm_active = self.settings.has_llm_credentials

        case_results: list[EvalCaseResult] = []
        retrieval_metrics: list[RetrievalCaseMetrics] = []
        ticket_metrics: list[TicketIntelligenceCaseMetrics] = []

        for case in cases_to_run:
            case_outcome, retrieval_metric, ticket_metric = self._run_case(engine, case, llm_active)
            case_results.append(case_outcome)
            if retrieval_metric is not None:
                retrieval_metrics.append(retrieval_metric)
            if ticket_metric is not None:
                ticket_metrics.append(ticket_metric)

        passed_count = sum(1 for case in case_results if case.status == "passed")
        failed_count = sum(1 for case in case_results if case.status == "failed")
        skipped_count = sum(1 for case in case_results if case.status == "skipped")
        errored_count = sum(1 for case in case_results if case.status == "errored")
        case_count_aggregated = passed_count + failed_count

        run_llm_used = any(
            case.llm_used for case in case_results if case.status in {"passed", "failed"}
        )

        retrieval_backend = "unknown"
        for case in case_results:
            if case.status in {"passed", "failed"} and case.query_result is not None:
                diagnostics = case.query_result.get("retrieval_diagnostics") or {}
                backend = diagnostics.get("backend") if isinstance(diagnostics, dict) else None
                if isinstance(backend, str) and backend:
                    retrieval_backend = backend
                    break

        retrieval_summary = summarize_retrieval_metrics(retrieval_metrics).to_dict()
        ticket_summary = summarize_ticket_intelligence_metrics(ticket_metrics).to_dict()

        finished_at = self._utc_now_iso()

        summary = EvalRunSummary(
            case_count_total=len(case_results),
            case_count_aggregated=case_count_aggregated,
            passed_count=passed_count,
            failed_count=failed_count,
            skipped_count=skipped_count,
            errored_count=errored_count,
            llm_used=run_llm_used,
            retrieval=retrieval_summary,
            ticket_intelligence=ticket_summary,
        )

        meta = EvalRunMeta(
            schema_version=SCHEMA_VERSION,
            run_started_at=started_at,
            run_finished_at=finished_at,
            llm_used=run_llm_used,
            retrieval_backend=retrieval_backend,
            dataset=dataset.dataset,
            dataset_path=str(dataset_path),
            dataset_hash=dataset_hash,
            command_args=tuple(command_args) if command_args is not None else (),
        )

        return EvalRunResult(meta=meta, summary=summary, cases=tuple(case_results))

    def _run_case(
        self, engine: RagEngine, case: EvaluationCase, llm_active: bool
    ) -> tuple[EvalCaseResult, RetrievalCaseMetrics | None, TicketIntelligenceCaseMetrics | None]:
        if case.expected_llm_answer is not None and not llm_active:
            return (
                EvalCaseResult(
                    case_id=case.id,
                    query=case.query,
                    status="skipped",
                    skip_reason="llm_required",
                    error=None,
                    llm_used=False,
                    query_result=None,
                    retrieval_metrics=None,
                    ticket_metrics=None,
                    expected_sources=case.expected_sources,
                    forbidden_sources=case.forbidden_sources,
                    actual_sources=(),
                    expected_llm_answer=case.expected_llm_answer,
                ),
                None,
                None,
            )

        try:
            query_result: QueryResult = engine.query(case.query)
        except IndexMissingError:
            # D-09: hard error — let it bubble out so the CLI can map to exit 1.
            raise
        except Exception:  # noqa: BLE001 — D-10 isolation requires catching all
            # D-10: per-case crash — capture stacktrace and continue.
            return (
                EvalCaseResult(
                    case_id=case.id,
                    query=case.query,
                    status="errored",
                    skip_reason=None,
                    error=traceback.format_exc()[:2000],
                    llm_used=False,
                    query_result=None,
                    retrieval_metrics=None,
                    ticket_metrics=None,
                    expected_sources=case.expected_sources,
                    forbidden_sources=case.forbidden_sources,
                    actual_sources=(),
                    expected_llm_answer=case.expected_llm_answer,
                ),
                None,
                None,
            )

        retrieval_metric = evaluate_retrieval_case(case, query_result.sources)
        ticket_metric = evaluate_ticket_intelligence_case(case, query_result.analysis)

        passed = (
            retrieval_metric.hit_at_5
            and not retrieval_metric.forbidden_hit
            and ticket_metric.intent_match
            and ticket_metric.routing_match
            and ticket_metric.identifier_recall == 1.0
            and ticket_metric.command_risk_accuracy == 1.0
            and ticket_metric.uncertainty_match
        )
        status = "passed" if passed else "failed"

        actual_sources = tuple(
            {"path": source.path, "score": source.score} for source in query_result.sources
        )

        return (
            EvalCaseResult(
                case_id=case.id,
                query=case.query,
                status=status,
                skip_reason=None,
                error=None,
                llm_used=query_result.llm_used,
                query_result=query_result.to_dict(),
                retrieval_metrics=retrieval_metric.to_dict(),
                ticket_metrics=ticket_metric.to_dict(),
                expected_sources=case.expected_sources,
                forbidden_sources=case.forbidden_sources,
                actual_sources=actual_sources,
                expected_llm_answer=case.expected_llm_answer,
            ),
            retrieval_metric,
            ticket_metric,
        )

    @staticmethod
    def _utc_now_iso() -> str:
        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


__all__ = [
    "SCHEMA_VERSION",
    "EvalCaseResult",
    "EvalRunMeta",
    "EvalRunResult",
    "EvalRunSummary",
    "EvalRunner",
    "EvalRunnerError",
]
