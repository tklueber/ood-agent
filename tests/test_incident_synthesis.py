from __future__ import annotations

from pathlib import Path

from pydantic import SecretStr

from ood.config import Settings
from ood.incident_synthesis import build_incident_solution_proposal
from ood.models import ConfidenceScore, QueryResult, RetrievalDiagnostics, RoutingDecision, SourceHit, TicketAnalysis


def _settings(tmp_path: Path, *, allow: bool = False) -> Settings:
    return Settings(
        knowledge_dir=tmp_path / "knowledge",
        data_dir=tmp_path / "data",
        storage_dir=tmp_path / "storage",
        llm_api_key=SecretStr("secret") if allow else None,
        allow_cloud_llm=allow,
    )


def _analysis() -> TicketAnalysis:
    return TicketAnalysis(
        intent="Problem",
        assessment=None,
        solution_steps=[],
        routing=RoutingDecision(route="selbst lösen", rationale="Actionable"),
        identifiers=[],
        command_risks=[],
        uncertainties=["Quelle prüfen"],
        mode="deterministic",
    )


def _query(*, answer: str | None = "Lösung aus Quellen", sources: list[SourceHit] | None = None, llm_used: bool = False) -> QueryResult:
    return QueryResult(
        query="TraceId Kafka",
        answer=answer,
        confidence=ConfidenceScore(score=0.8, rationale="Gute Treffer"),
        sources=sources if sources is not None else [SourceHit(path="a.md", score=0.9, excerpt="A"), SourceHit(path="b.md", score=0.7, excerpt="B")],
        llm_used=llm_used,
        status="success",
        analysis=_analysis(),
        retrieval_diagnostics=RetrievalDiagnostics(backend="local", strategy="hybrid"),
    )


def test_local_query_result_becomes_extractive_proposal(tmp_path: Path) -> None:
    proposal = build_incident_solution_proposal(_query(), _settings(tmp_path))

    assert proposal.synthesis_mode == "local_extractive"
    assert proposal.llm_used is False
    assert len(proposal.suggestion_id) == 16
    assert proposal.citations[0]["path"] == "a.md"
    assert proposal.citations[0]["score"] == 0.9


def test_no_sources_and_no_answer_is_no_results(tmp_path: Path) -> None:
    proposal = build_incident_solution_proposal(_query(answer=None, sources=[]), _settings(tmp_path))

    assert proposal.synthesis_mode == "no_results"
    assert proposal.proposal is None


def test_suggestion_id_is_deterministic(tmp_path: Path) -> None:
    first = build_incident_solution_proposal(_query(), _settings(tmp_path))
    second = build_incident_solution_proposal(_query(), _settings(tmp_path))

    assert first.suggestion_id == second.suggestion_id
    assert len(first.suggestion_id) == 16


def test_privacy_gate_is_exposed_without_mutating_llm_used(tmp_path: Path) -> None:
    proposal = build_incident_solution_proposal(_query(llm_used=True), _settings(tmp_path))

    payload = proposal.to_dict()

    assert payload["llm_allowed"] is False
    assert payload["llm_used"] is True


def test_llm_grounded_preserves_deterministic_analysis(tmp_path: Path) -> None:
    proposal = build_incident_solution_proposal(_query(llm_used=True), _settings(tmp_path, allow=True))
    payload = proposal.to_dict()

    assert proposal.synthesis_mode == "llm_grounded"
    assert payload["analysis"] == _analysis().to_dict()
    assert payload["confidence"] == {"score": 0.8, "rationale": "Gute Treffer"}
    assert payload["retrieval_diagnostics"]["backend"] == "local"


def test_synthesis_module_uses_can_use_cloud_llm_not_credentials() -> None:
    source = Path("src/ood/incident_synthesis.py").read_text(encoding="utf-8")

    assert "can_use_cloud_llm" in source
    assert "has_llm_credentials" not in source
