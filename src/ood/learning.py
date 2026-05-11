from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _validate_rating(name: str, value: int) -> None:
    if not isinstance(value, int) or value < 1 or value > 5:
        raise ValueError(f"{name} must be an integer from 1 through 5")


def record_feedback(
    *,
    data_dir: Path,
    suggestion_id: str,
    solved: bool,
    useful: int,
    correct: int,
    routing_correct: bool,
    missing_evidence: str | None,
) -> Path:
    _validate_rating("useful", useful)
    _validate_rating("correct", correct)
    return _write_json(
        data_dir / "feedback" / f"{suggestion_id}.feedback.json",
        {
            "schema_version": 1,
            "suggestion_id": suggestion_id,
            "solved": solved,
            "useful": useful,
            "correct": correct,
            "routing_correct": routing_correct,
            "missing_evidence": missing_evidence or "",
            "recorded_at": _timestamp(),
        },
    )


def record_actual_resolution(
    *,
    data_dir: Path,
    suggestion_id: str,
    resolution_text: str,
    resolver: str | None,
    source_ticket: str | None,
) -> Path:
    return _write_json(
        data_dir / "resolutions" / f"{suggestion_id}.resolution.json",
        {
            "schema_version": 1,
            "suggestion_id": suggestion_id,
            "resolution_text": resolution_text,
            "resolver": resolver or "",
            "source_ticket": source_ticket or "",
            "recorded_at": _timestamp(),
        },
    )


def _load_optional(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def create_knowledge_update_proposal(*, data_dir: Path, suggestion_id: str) -> Path:
    feedback_path = data_dir / "feedback" / f"{suggestion_id}.feedback.json"
    resolution_path = data_dir / "resolutions" / f"{suggestion_id}.resolution.json"
    feedback = _load_optional(feedback_path)
    resolution = _load_optional(resolution_path)
    source_artifacts = [str(path) for path in (feedback_path, resolution_path) if path.exists()]
    resolution_text = (resolution or {}).get("resolution_text", "")
    missing_evidence = (feedback or {}).get("missing_evidence", "")
    payload = {
        "schema_version": 1,
        "suggestion_id": suggestion_id,
        "review_status": "pending",
        "created_at": _timestamp(),
        "proposed_frontmatter": {
            "title": "",
            "type": "incident",
            "status": "draft",
            "system": "",
            "komponente": "",
            "keywords": [],
            "aliases": [],
            "related": [],
            "owner": "",
            "last_verified": "",
            "source_constraints": ["review_required", "not_auto_indexed"],
        },
        "proposed_body": "\n".join(
            [
                "## Problem",
                "Noch aus Ticketkontext ergänzen.",
                "",
                "## Tatsächliche Lösung",
                str(resolution_text),
                "",
                "## Evidenz",
                str(missing_evidence),
                "",
                "## Review-Notizen",
                "Vor dem Kopieren in die Knowledge Base fachlich prüfen.",
            ]
        ),
        "source_artifacts": source_artifacts,
    }
    return _write_json(data_dir / "knowledge-proposals" / f"{suggestion_id}.proposal.json", payload)


__all__ = ["record_feedback", "record_actual_resolution", "create_knowledge_update_proposal"]
