from __future__ import annotations

import json
from pathlib import Path

from ood.config import Settings
from ood.mock_corpus import generate_mock_corpus
from ood.rag import LOCAL_VECTOR_INDEX_FILENAME, MANIFEST_FILENAME, RagEngine


def _mock_settings(tmp_path: Path) -> Settings:
    return Settings(
        knowledge_dir=tmp_path / "knowledge" / "mock" / "v1",
        data_dir=tmp_path / "data",
        storage_dir=tmp_path / "data" / "storage",
    )


def test_generated_mock_corpus_indexes_as_normal_knowledge(tmp_path: Path, monkeypatch) -> None:
    settings = _mock_settings(tmp_path)
    corpus = generate_mock_corpus(settings.knowledge_dir)
    monkeypatch.setattr("ood.rag.LightRAG", None)
    monkeypatch.setattr(RagEngine, "_encode_local_embeddings", lambda self, texts: [[1.0, 0.0] for _ in texts])

    result = RagEngine(settings).index_markdown()

    assert result.status == "indexed"
    assert result.indexed_documents == corpus.document_count
    assert result.skipped_documents == 0
    assert result.metadata_warnings == []
    assert result.manifest_path == settings.storage_dir / MANIFEST_FILENAME

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    entries = manifest["entries"]
    expected_paths = sorted(path.relative_to(settings.knowledge_dir).as_posix() for path in corpus.generated_paths)
    assert len(entries) == corpus.document_count
    assert [entry["path"] for entry in entries] == expected_paths

    required_metadata = {"quelle", "datum", "status", "system", "komponente", "title", "type"}
    for entry in entries:
        metadata = entry["metadata"]
        assert metadata["mock"] == "true"
        assert metadata["dataset"] == "mock-v1"
        assert metadata["synthetic_id"].startswith("MOCK-")
        assert metadata["source_type"] in corpus.source_types
        assert required_metadata <= set(metadata)
        assert all(metadata[field] for field in required_metadata)

    fallback = json.loads((settings.storage_dir / LOCAL_VECTOR_INDEX_FILENAME).read_text(encoding="utf-8"))
    documents = fallback["documents"]
    assert [document["path"] for document in documents] == expected_paths
    assert len(documents) == corpus.document_count
    for document in documents:
        content = document["content"]
        assert document["vector"] == [1.0, 0.0]
        assert document["excerpt"] == content[:500]
        assert "MOCK DATA" in content
        assert "mock: true" not in content
        assert "synthetic_id:" not in content
        assert content.lstrip().startswith("⚠️ MOCK DATA / SYNTHETIC")


def test_mock_reindex_cleans_storage_without_touching_mock_corpus_or_data_siblings(
    tmp_path: Path, monkeypatch
) -> None:
    settings = _mock_settings(tmp_path)
    corpus = generate_mock_corpus(settings.knowledge_dir)
    original_contents = {path: path.read_text(encoding="utf-8") for path in corpus.generated_paths}
    settings.storage_dir.mkdir(parents=True)
    stale_file = settings.storage_dir / "old-vector.json"
    stale_file.write_text("old", encoding="utf-8")
    stale_nested = settings.storage_dir / "nested"
    stale_nested.mkdir()
    (stale_nested / "old-graph.json").write_text("old", encoding="utf-8")
    sibling_file = settings.data_dir / "outside-storage.txt"
    sibling_file.write_text("keep", encoding="utf-8")
    monkeypatch.setattr("ood.rag.LightRAG", None)
    monkeypatch.setattr(RagEngine, "_encode_local_embeddings", lambda self, texts: [[1.0, 0.0] for _ in texts])

    result = RagEngine(settings).reindex_markdown()

    assert result.status == "indexed"
    assert result.indexed_documents == corpus.document_count
    assert result.skipped_documents == 0
    assert not stale_file.exists()
    assert not stale_nested.exists()
    assert sibling_file.read_text(encoding="utf-8") == "keep"
    assert {path: path.read_text(encoding="utf-8") for path in corpus.generated_paths} == original_contents

    manifest = json.loads((settings.storage_dir / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    expected_paths = sorted(path.relative_to(settings.knowledge_dir).as_posix() for path in corpus.generated_paths)
    manifest_paths = [entry["path"] for entry in manifest["entries"]]
    assert manifest_paths == expected_paths
    assert "old-vector.json" not in manifest_paths
    assert "outside-storage.txt" not in manifest_paths
