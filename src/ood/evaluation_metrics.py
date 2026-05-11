from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Iterable

from ood.evaluation import EvaluationCase
from ood.models import SourceHit


@dataclass(frozen=True)
class RetrievalCaseMetrics:
    case_id: str
    hit_at_1: bool
    hit_at_3: bool
    hit_at_5: bool
    mrr: float
    source_recall: float
    forbidden_hit: bool
    forbidden_hit_paths: tuple[str, ...]
    first_relevant_rank: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "Hit@1": self.hit_at_1,
            "Hit@3": self.hit_at_3,
            "Hit@5": self.hit_at_5,
            "mrr": self.mrr,
            "source_recall": self.source_recall,
            "forbidden_hit": self.forbidden_hit,
            "forbidden_hit_paths": list(self.forbidden_hit_paths),
            "first_relevant_rank": self.first_relevant_rank,
        }


@dataclass(frozen=True)
class RetrievalMetricsSummary:
    case_count: int
    hit_at_1: float
    hit_at_3: float
    hit_at_5: float
    mrr: float
    source_recall: float
    forbidden_source_rate: float

    def to_dict(self) -> dict[str, int | float]:
        return {
            "case_count": self.case_count,
            "Hit@1": self.hit_at_1,
            "Hit@3": self.hit_at_3,
            "Hit@5": self.hit_at_5,
            "mrr": self.mrr,
            "source_recall": self.source_recall,
            "forbidden_source_rate": self.forbidden_source_rate,
        }


def evaluate_retrieval_case(case: EvaluationCase, sources: list[SourceHit]) -> RetrievalCaseMetrics:
    """Compute deterministic retrieval metrics for one evaluation case."""

    expected_paths = {_normalize_path(path) for path in case.expected_sources}
    forbidden_paths = {_normalize_path(path) for path in case.forbidden_sources}
    ranked_paths = [_normalize_path(source.path) for source in sources]

    first_relevant_rank = _first_relevant_rank(ranked_paths, expected_paths)
    unique_returned = set(ranked_paths)
    matched_expected = expected_paths & unique_returned
    forbidden_hits = tuple(path for path in ranked_paths if path in forbidden_paths)
    unique_forbidden_hits = tuple(dict.fromkeys(forbidden_hits))

    return RetrievalCaseMetrics(
        case_id=case.id,
        hit_at_1=_has_hit_at(ranked_paths, expected_paths, 1),
        hit_at_3=_has_hit_at(ranked_paths, expected_paths, 3),
        hit_at_5=_has_hit_at(ranked_paths, expected_paths, 5),
        mrr=0.0 if first_relevant_rank is None else 1.0 / first_relevant_rank,
        source_recall=0.0 if not expected_paths else len(matched_expected) / len(expected_paths),
        forbidden_hit=bool(unique_forbidden_hits),
        forbidden_hit_paths=unique_forbidden_hits,
        first_relevant_rank=first_relevant_rank,
    )


def summarize_retrieval_metrics(metrics: list[RetrievalCaseMetrics]) -> RetrievalMetricsSummary:
    """Aggregate per-case retrieval metrics into stable report-ready rates."""

    case_count = len(metrics)
    if case_count == 0:
        return RetrievalMetricsSummary(
            case_count=0,
            hit_at_1=0.0,
            hit_at_3=0.0,
            hit_at_5=0.0,
            mrr=0.0,
            source_recall=0.0,
            forbidden_source_rate=0.0,
        )

    return RetrievalMetricsSummary(
        case_count=case_count,
        hit_at_1=_rounded_mean(1.0 if metric.hit_at_1 else 0.0 for metric in metrics),
        hit_at_3=_rounded_mean(1.0 if metric.hit_at_3 else 0.0 for metric in metrics),
        hit_at_5=_rounded_mean(1.0 if metric.hit_at_5 else 0.0 for metric in metrics),
        mrr=_rounded_mean(metric.mrr for metric in metrics),
        source_recall=_rounded_mean(metric.source_recall for metric in metrics),
        forbidden_source_rate=_rounded_mean(1.0 if metric.forbidden_hit else 0.0 for metric in metrics),
    )


def _has_hit_at(ranked_paths: list[str], expected_paths: set[str], k: int) -> bool:
    return any(path in expected_paths for path in ranked_paths[:k])


def _first_relevant_rank(ranked_paths: list[str], expected_paths: set[str]) -> int | None:
    for index, path in enumerate(ranked_paths, start=1):
        if path in expected_paths:
            return index
    return None


def _normalize_path(path: str) -> str:
    posix = path.replace("\\", "/")
    return PurePosixPath(posix).as_posix().removeprefix("./")


def _rounded_mean(values: Iterable[float]) -> float:
    value_list = list(values)
    if not value_list:
        return 0.0
    return round(sum(value_list) / len(value_list), 4)


__all__ = [
    "RetrievalCaseMetrics",
    "RetrievalMetricsSummary",
    "evaluate_retrieval_case",
    "summarize_retrieval_metrics",
]
