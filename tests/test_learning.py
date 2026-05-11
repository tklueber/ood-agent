from __future__ import annotations

import json
from pathlib import Path

import pytest

from ood.learning import create_knowledge_update_proposal, record_actual_resolution, record_feedback


def test_record_feedback_writes_artifact(tmp_path: Path) -> None:
    path = record_feedback(
        data_dir=tmp_path,
        suggestion_id="abc123",
        solved=True,
        useful=5,
        correct=4,
        routing_correct=True,
        missing_evidence="",
    )

    assert path == tmp_path / "feedback" / "abc123.feedback.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["suggestion_id"] == "abc123"
    assert payload["solved"] is True
    assert payload["useful"] == 5
    assert payload["correct"] == 4
    assert payload["routing_correct"] is True
    assert payload["missing_evidence"] == ""
    assert payload["recorded_at"].endswith("Z")


def test_record_feedback_validates_rating_range(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        record_feedback(data_dir=tmp_path, suggestion_id="abc123", solved=True, useful=6, correct=4, routing_correct=True, missing_evidence=None)
    with pytest.raises(ValueError):
        record_feedback(data_dir=tmp_path, suggestion_id="abc123", solved=True, useful=5, correct=0, routing_correct=True, missing_evidence=None)


def test_record_actual_resolution_writes_linked_artifact(tmp_path: Path) -> None:
    path = record_actual_resolution(
        data_dir=tmp_path,
        suggestion_id="abc123",
        resolution_text="Kafka Offset neu gelesen",
        resolver="Timo",
        source_ticket="INC001",
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert path == tmp_path / "resolutions" / "abc123.resolution.json"
    assert payload["suggestion_id"] == "abc123"
    assert payload["resolution_text"] == "Kafka Offset neu gelesen"
    assert payload["resolver"] == "Timo"
    assert payload["source_ticket"] == "INC001"


def test_create_knowledge_update_proposal_is_pending(tmp_path: Path) -> None:
    feedback = record_feedback(data_dir=tmp_path, suggestion_id="abc123", solved=True, useful=5, correct=4, routing_correct=True, missing_evidence="Log fehlt")
    resolution = record_actual_resolution(data_dir=tmp_path, suggestion_id="abc123", resolution_text="Kafka Offset neu gelesen", resolver="Timo", source_ticket="INC001")

    path = create_knowledge_update_proposal(data_dir=tmp_path, suggestion_id="abc123")

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert path == tmp_path / "knowledge-proposals" / "abc123.proposal.json"
    assert payload["review_status"] == "pending"
    assert payload["review_status"] != "approved"
    assert "proposed_frontmatter" in payload
    assert "proposed_body" in payload
    assert "## Problem" in payload["proposed_body"]
    assert "## Tatsächliche Lösung" in payload["proposed_body"]
    assert str(feedback) in payload["source_artifacts"]
    assert str(resolution) in payload["source_artifacts"]
