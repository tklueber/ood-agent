from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from ood.config import Settings
from ood.models import QueryResult


@dataclass(frozen=True)
class IncidentSolutionProposal:
    suggestion_id: str
    synthesis_mode: str
    proposal: str | None
    citations: list[dict[str, object]]
    confidence: dict[str, object]
    llm_used: bool
    llm_allowed: bool
    analysis: dict[str, object]
    retrieval_diagnostics: dict[str, object]
    uncertainties: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "suggestion_id": self.suggestion_id,
            "synthesis_mode": self.synthesis_mode,
            "proposal": self.proposal,
            "citations": self.citations,
            "confidence": self.confidence,
            "llm_used": self.llm_used,
            "llm_allowed": self.llm_allowed,
            "analysis": self.analysis,
            "retrieval_diagnostics": self.retrieval_diagnostics,
            "uncertainties": self.uncertainties,
        }


def build_incident_solution_proposal(query_result: QueryResult, settings: Settings) -> IncidentSolutionProposal:
    """Normalize a QueryResult into a grounded operational proposal artifact."""

    joined_paths = "|".join(source.path for source in query_result.sources)
    digest = hashlib.sha256(f"{query_result.query}|{joined_paths}|{query_result.answer or ''}".encode("utf-8")).hexdigest()[:16]
    citations: list[dict[str, object]] = [
        {"path": source.path, "score": source.score, "excerpt": source.excerpt[:500]}
        for source in query_result.sources
    ]
    if not query_result.answer and not query_result.sources:
        mode = "no_results"
        proposal = None
    elif query_result.llm_used:
        mode = "llm_grounded"
        proposal = query_result.answer
    else:
        mode = "local_extractive"
        proposal = query_result.answer

    return IncidentSolutionProposal(
        suggestion_id=digest,
        synthesis_mode=mode,
        proposal=proposal,
        citations=citations,
        confidence=query_result.confidence.to_dict(),
        llm_used=query_result.llm_used,
        llm_allowed=settings.can_use_cloud_llm,
        analysis=query_result.analysis.to_dict(),
        retrieval_diagnostics=query_result.retrieval_diagnostics.to_dict(),
        uncertainties=query_result.analysis.uncertainties,
    )


__all__ = ["IncidentSolutionProposal", "build_incident_solution_proposal"]
