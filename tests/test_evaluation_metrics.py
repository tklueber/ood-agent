from ood.evaluation import EvaluationCase
from ood.evaluation_metrics import evaluate_retrieval_case, summarize_retrieval_metrics
from ood.models import SourceHit


def _case(
    *,
    expected_sources: tuple[str, ...] = ("B.md",),
    forbidden_sources: tuple[str, ...] = (),
) -> EvaluationCase:
    return EvaluationCase(
        id="case-1",
        query="query",
        expected_sources=expected_sources,
        forbidden_sources=forbidden_sources,
        expected_intent="Problem",
        expected_route="selbst lösen",
        expected_identifiers=(),
        expected_command_risks=(),
        expected_uncertainties=(),
    )


def _source(path: str) -> SourceHit:
    return SourceHit(path=path, score=1.0, excerpt="excerpt")


def test_evaluate_retrieval_case_computes_ranked_hit_mrr_and_recall() -> None:
    metrics = evaluate_retrieval_case(_case(expected_sources=("B.md",)), [_source("A.md"), _source("B.md"), _source("C.md")])

    assert metrics.hit_at_1 is False
    assert metrics.hit_at_3 is True
    assert metrics.hit_at_5 is True
    assert metrics.mrr == 0.5
    assert metrics.source_recall == 1.0
    assert metrics.first_relevant_rank == 2
    assert metrics.to_dict()["Hit@5"] is True


def test_evaluate_retrieval_case_uses_unique_matches_for_recall_and_forbidden() -> None:
    metrics = evaluate_retrieval_case(
        _case(
            expected_sources=("ticket/mock-pol-1001.md", "wiki/mock-wiki-5001.md"),
            forbidden_sources=("note/mock-note-7002.md",),
        ),
        [
            _source("./ticket/mock-pol-1001.md"),
            _source("ticket/mock-pol-1001.md"),
            _source("note/mock-note-7002.md"),
        ],
    )

    assert metrics.source_recall == 0.5
    assert metrics.forbidden_hit is True
    assert metrics.forbidden_hit_paths == ("note/mock-note-7002.md",)


def test_evaluate_retrieval_case_handles_empty_sources() -> None:
    metrics = evaluate_retrieval_case(_case(), [])

    assert metrics.hit_at_1 is False
    assert metrics.hit_at_3 is False
    assert metrics.hit_at_5 is False
    assert metrics.mrr == 0.0
    assert metrics.source_recall == 0.0
    assert metrics.forbidden_hit is False


def test_summarize_retrieval_metrics_averages_case_values() -> None:
    metrics = [
        evaluate_retrieval_case(_case(expected_sources=("A.md",)), [_source("A.md")]),
        evaluate_retrieval_case(
            _case(expected_sources=("B.md", "C.md"), forbidden_sources=("X.md",)),
            [_source("A.md"), _source("B.md"), _source("X.md")],
        ),
    ]

    summary = summarize_retrieval_metrics(metrics)

    assert summary.case_count == 2
    assert summary.hit_at_1 == 0.5
    assert summary.hit_at_3 == 1.0
    assert summary.hit_at_5 == 1.0
    assert summary.mrr == 0.75
    assert summary.source_recall == 0.75
    assert summary.forbidden_source_rate == 0.5
    assert summary.to_dict() == {
        "case_count": 2,
        "Hit@1": 0.5,
        "Hit@3": 1.0,
        "Hit@5": 1.0,
        "mrr": 0.75,
        "source_recall": 0.75,
        "forbidden_source_rate": 0.5,
    }


def test_summarize_retrieval_metrics_handles_empty_lists() -> None:
    summary = summarize_retrieval_metrics([])

    assert summary.case_count == 0
    assert summary.hit_at_1 == 0.0
    assert summary.hit_at_3 == 0.0
    assert summary.hit_at_5 == 0.0
    assert summary.mrr == 0.0
    assert summary.source_recall == 0.0
    assert summary.forbidden_source_rate == 0.0
