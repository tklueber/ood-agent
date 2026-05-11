from __future__ import annotations

import asyncio
import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from collections.abc import Awaitable, Callable
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import numpy as np

from ood.config import Settings
from ood.models import (
    ConfidenceScore,
    DuplicateGroup,
    IndexMissingError,
    IndexResult,
    IndexStatus,
    ManifestDiff,
    ManifestEntry,
    MetadataWarning,
    QueryResult,
    RetrievalDiagnostics,
    SourceHit,
    SourceScoreBreakdown,
    TicketAnalysis,
    UpdateResult,
)
from ood.ticket_intelligence import analyze_ticket


LOCAL_EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
LOCAL_EMBEDDING_DIM = 384
MAX_EMBEDDING_TOKENS = 8192
FALLBACK_INDEX_FILENAME = "ood-fallback-index.json"
LOCAL_VECTOR_INDEX_FILENAME = "ood-local-vector-index.json"
LOCAL_GRAPH_INDEX_FILENAME = "ood-local-graph-index.json"
QUERY_SOURCE_LIMIT = 5
HYBRID_SEMANTIC_WEIGHT = 0.65
HYBRID_LEXICAL_WEIGHT = 0.35
HYBRID_GRAPH_SEMANTIC_WEIGHT = 0.20
HYBRID_GRAPH_LEXICAL_WEIGHT = 0.15
HYBRID_GRAPH_METADATA_WEIGHT = 0.40
HYBRID_GRAPH_GRAPH_WEIGHT = 0.25
HYBRID_EXACT_TOKEN_BOOST = 0.35
MANIFEST_SCHEMA_VERSION = 1
MANIFEST_FILENAME = "ood-manifest.json"
REQUIRED_METADATA_FIELDS = ("quelle", "datum", "status", "system", "komponente", "title", "type")
VALID_STATUS_VALUES = ("active", "deprecated", "draft")


LightRAG: type[Any] | None = None
openai_complete_if_cache: Callable[..., Awaitable[str]] | None = None


@dataclass(frozen=True)
class _ParsedMarkdownDocument:
    path: Path
    relative_path: str
    raw_content: str
    body_text: str
    metadata: dict[str, str]
    warnings: list[MetadataWarning]
    content_hash: str
    body_hash: str
    body_excerpt: str


class RagEngine:
    """Service-layer adapter for Markdown indexing into LightRAG storage."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def index_markdown(self) -> IndexResult:
        """Index Markdown documents without clearing existing LightRAG storage."""

        return asyncio.run(self._aindex_markdown(clear_storage=False))

    def query(self, query_text: str) -> QueryResult:
        """Query the existing LightRAG index and return the stable OOD contract."""

        return asyncio.run(self._aquery(query_text))

    def update_markdown(self) -> UpdateResult:
        """Incrementally index new and changed Markdown documents using the manifest."""

        return asyncio.run(self._aupdate_markdown())

    def status(self) -> IndexStatus:
        """Return local knowledge and retrieval artifact diagnostics."""

        storage_dir = self.settings.storage_dir
        if storage_dir is None:
            msg = "storage_dir is not configured."
            raise ValueError(msg)

        knowledge_documents = len(self._discover_markdown_files())
        manifest = self._read_manifest()
        entries = manifest.get("entries", []) if manifest is not None else []
        indexed_documents = len(entries) if isinstance(entries, list) else 0
        chunks = self._count_local_vector_documents()
        storage_files = 0
        if storage_dir.exists():
            storage_files = sum(1 for path in storage_dir.rglob("*") if path.is_file())

        if indexed_documents or chunks:
            status = "ready"
            message = "Knowledge index artifacts are present."
        elif knowledge_documents:
            status = "not_indexed"
            message = "Markdown documents exist, but no index artifacts were found. Run `ood index`."
        else:
            status = "empty"
            message = "No Markdown documents or index artifacts found."

        return IndexStatus(
            status=status,
            knowledge_dir=self.settings.knowledge_dir,
            data_dir=self.settings.data_dir,
            storage_dir=storage_dir,
            manifest_path=self._manifest_path(),
            vector_index_path=self._fallback_index_path,
            knowledge_documents=knowledge_documents,
            indexed_documents=indexed_documents,
            chunks=chunks,
            storage_files=storage_files,
            message=message,
        )

    async def _aupdate_markdown(self) -> UpdateResult:
        self.settings.storage_dir.mkdir(parents=True, exist_ok=True)
        manifest = self._read_manifest()
        if manifest is not None:
            self._validate_manifest_schema(manifest)
        previous_entries = self._manifest_entries_by_path(manifest) if manifest is not None else {}
        parsed_documents, skipped_documents = self._load_parsed_markdown_documents()
        diff = self._build_manifest_diff(parsed_documents, previous_entries)
        touched_paths = set(diff.new_paths + diff.changed_paths)
        touched_documents = [parsed for parsed in parsed_documents if parsed.relative_path in touched_paths]
        duplicate_groups = self._detect_duplicates(parsed_documents, touched_paths=touched_paths or None)
        manifest_entries = self._build_manifest_entries(parsed_documents, duplicate_groups)
        metadata_warnings = [warning for parsed in parsed_documents for warning in parsed.warnings]

        if touched_documents:
            documents = [parsed.body_text for parsed in touched_documents]
            relative_paths = [parsed.relative_path for parsed in touched_documents]
            if self._should_use_local_fallback():
                self._write_local_fallback_index(
                    [parsed.body_text for parsed in parsed_documents],
                    [parsed.relative_path for parsed in parsed_documents],
                )
            else:
                rag = self._build_lightrag()
                await rag.ainsert(documents, file_paths=relative_paths)

        self._write_manifest(manifest_entries, duplicate_groups)
        if parsed_documents:
            self._write_local_graph_index(parsed_documents)

        if touched_documents:
            status = "updated"
            message = f"Updated {len(touched_documents)} Markdown document(s)."
        elif diff.deleted_paths:
            status = "stale_entries"
            message = f"Detected {len(diff.deleted_paths)} stale/deleted knowledge file(s). Run `ood reindex` to clean up."
        elif not parsed_documents and not previous_entries:
            status = "no_documents"
            message = "No Markdown documents found to update."
        else:
            status = "no_changes"
            message = "No knowledge changes detected."

        return UpdateResult(
            status=status,
            indexed_documents=len(touched_documents),
            skipped_documents=skipped_documents,
            storage_dir=self.settings.storage_dir,
            manifest_path=self._manifest_path(),
            message=message,
            diff=diff,
            metadata_warnings=metadata_warnings,
            duplicate_groups=duplicate_groups,
            schema_version=MANIFEST_SCHEMA_VERSION,
        )

    async def _aquery(self, query_text: str) -> QueryResult:
        self._ensure_index_exists()

        if self._should_use_local_fallback():
            sources = self._query_local_fallback(query_text)
            retrieval_diagnostics = getattr(self, "_last_retrieval_diagnostics", self._local_retrieval_diagnostics([]))
            answer = self._synthesize_extractive_answer(query_text, sources)
            confidence = self._score_confidence(sources, llm_used=False)
            analysis = analyze_ticket(query_text, sources, confidence)
            if answer is not None:
                analysis = self._enrich_analysis_with_local_answer(analysis, answer)
            return QueryResult(
                query=query_text,
                answer=answer,
                confidence=confidence,
                sources=sources,
                llm_used=False,
                status="success" if sources else "no_results",
                analysis=analysis,
                retrieval_diagnostics=retrieval_diagnostics,
            )

        from lightrag import QueryParam

        rag = self._build_lightrag()
        query_param = (
            QueryParam(mode="mix", top_k=QUERY_SOURCE_LIMIT, chunk_top_k=QUERY_SOURCE_LIMIT)
            if self.settings.can_use_cloud_llm and self._supports_llm_provider()
            else QueryParam(mode="naive", top_k=QUERY_SOURCE_LIMIT, chunk_top_k=QUERY_SOURCE_LIMIT)
        )
        data = await rag.aquery_data(query_text, query_param)
        sources = self._normalize_sources(data)
        answer: str | None = None
        if self.settings.can_use_cloud_llm and self._supports_llm_provider() and hasattr(rag, "aquery"):
            generated_answer = await rag.aquery(query_text, param=query_param)
            if isinstance(generated_answer, str) and generated_answer.strip():
                answer = generated_answer.strip()
        llm_used = answer is not None
        confidence = self._score_confidence(sources, llm_used)
        analysis = analyze_ticket(query_text, sources, confidence)
        if llm_used and answer is not None:
            analysis = self._enrich_analysis_with_llm_answer(analysis, answer)
        retrieval_diagnostics = self._lightrag_retrieval_diagnostics(
            strategy="mix" if self.settings.can_use_cloud_llm and self._supports_llm_provider() else "naive",
            sources=sources,
        )
        return QueryResult(
            query=query_text,
            answer=answer,
            confidence=confidence,
            sources=sources,
            llm_used=llm_used,
            status="success" if sources else "no_results",
            analysis=analysis,
            retrieval_diagnostics=retrieval_diagnostics,
        )

    @staticmethod
    def _enrich_analysis_with_llm_answer(analysis: TicketAnalysis, answer: str) -> TicketAnalysis:
        steps: list[str] = []
        for line in answer.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            match = re.match(r"^(?:[-*]|\d+[.)])\s*(.+)$", stripped)
            if match:
                steps.append(match.group(1).strip())
            if len(steps) >= 5:
                break
        return TicketAnalysis(
            intent=analysis.intent,
            assessment=answer,
            solution_steps=steps,
            routing=analysis.routing,
            identifiers=analysis.identifiers,
            command_risks=analysis.command_risks,
            uncertainties=analysis.uncertainties,
            mode="llm_grounded",
        )

    @staticmethod
    def _enrich_analysis_with_local_answer(analysis: TicketAnalysis, answer: str) -> TicketAnalysis:
        steps: list[str] = []
        for line in answer.splitlines():
            stripped = line.strip()
            match = re.search(r"\[\d+\]\s*(?:\d+[.)]|[-*]|Bitte|Prüfe|Pruefe|Starte|Setze|Restart|Check|Use)\s*(.+)", stripped, re.IGNORECASE)
            if match:
                steps.append(match.group(0).strip())
            if len(steps) >= 5:
                break
        return TicketAnalysis(
            intent=analysis.intent,
            assessment=answer,
            solution_steps=steps,
            routing=analysis.routing,
            identifiers=analysis.identifiers,
            command_risks=analysis.command_risks,
            uncertainties=analysis.uncertainties,
            mode="local_extractive",
        )

    def _synthesize_extractive_answer(self, query_text: str, sources: list[SourceHit]) -> str | None:
        if not sources:
            return None
        query_tokens = self._tokenize(query_text)
        evidence: list[tuple[int, str]] = []
        for rank, source in enumerate(sources[:3], start=1):
            sentences = self._split_sentences(source.excerpt)
            ranked = sorted(
                sentences,
                key=lambda sentence: len(query_tokens & self._tokenize(sentence)),
                reverse=True,
            )
            for sentence in ranked:
                if sentence.strip():
                    evidence.append((rank, sentence.strip()))
                    break
        if not evidence:
            return None
        parts = [f"[{rank}] {sentence}" for rank, sentence in evidence]
        return "Gefundene Hinweise: " + " ".join(parts)

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        normalized = re.sub(r"\s+", " ", text).strip()
        if not normalized:
            return []
        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if part.strip()]
        return sentences or [normalized]

    def _supports_llm_provider(self) -> bool:
        return self.settings.llm_provider in (None, "openai", "openai-compatible")

    def _score_confidence(self, sources: list[SourceHit], llm_used: bool) -> ConfidenceScore:
        if not sources:
            return ConfidenceScore(score=0.0, rationale="No sources retrieved.")

        top_score = sources[0].score
        source_factor = min(len(sources), 3) / 3
        spread_factor = (
            1.0
            if len(sources) == 1
            else min(1.0, max(0.0, sources[0].score - sources[-1].score + 0.5))
        )
        llm_factor = 1.0 if llm_used else 0.7
        score = round(
            min(1.0, top_score * 0.5 + source_factor * 0.25 + spread_factor * 0.15 + llm_factor * 0.10),
            2,
        )
        if llm_used:
            rationale = "Confidence is based on retrieval strength, source coverage, score spread, and LLM availability."
        elif not self.settings.has_llm_credentials:
            rationale = (
                "Confidence is limited because no LLM credentials are configured; "
                "it is based on retrieval strength, source coverage, and score spread."
            )
        elif not self.settings.allow_cloud_llm:
            rationale = (
                "Confidence is limited because Cloud LLM usage is not privacy-approved; "
                "it is based on retrieval strength, source coverage, and score spread."
            )
        else:
            rationale = (
                "Confidence is limited because no LLM credentials are configured or provider is unsupported; "
                "it is based on retrieval strength, source coverage, and score spread."
            )
        return ConfidenceScore(score=score, rationale=rationale)

    def _ensure_index_exists(self) -> None:
        storage_dir = self.settings.storage_dir
        if storage_dir is None or not storage_dir.exists() or not any(storage_dir.iterdir()):
            msg = "No index found. Run `ood index` first."
            raise IndexMissingError(msg)

    def _normalize_sources(self, data: dict[str, Any]) -> list[SourceHit]:
        chunks = data.get("data", {}).get("chunks", [])
        if not isinstance(chunks, list):
            return []

        sources_by_path: dict[str, SourceHit] = {}
        for rank, chunk in enumerate(chunks):
            if not isinstance(chunk, dict):
                continue

            path = self._normalize_source_path(self._extract_path(chunk))
            excerpt = self._extract_excerpt(chunk)
            if not path or not excerpt:
                continue

            score = self._extract_score(chunk, rank)
            hit = SourceHit(path=path, score=score, excerpt=excerpt)
            existing = sources_by_path.get(path)
            if existing is None or hit.score > existing.score:
                sources_by_path[path] = hit

        return sorted(sources_by_path.values(), key=lambda source: source.score, reverse=True)[:QUERY_SOURCE_LIMIT]

    def _extract_path(self, chunk: dict[str, Any]) -> str | None:
        for key in ("file_path", "full_doc_id", "source"):
            value = chunk.get(key)
            if isinstance(value, str) and value.strip():
                return value

        metadata = chunk.get("metadata")
        if isinstance(metadata, dict):
            for key in ("file_path", "full_doc_id", "source"):
                value = metadata.get(key)
                if isinstance(value, str) and value.strip():
                    return value
        return None

    def _normalize_source_path(self, raw_path: str | None) -> str | None:
        if raw_path is None:
            return None

        path = Path(raw_path)
        if path.is_absolute():
            try:
                return path.relative_to(self.settings.knowledge_dir).as_posix()
            except ValueError:
                return path.name
        return path.as_posix()

    @staticmethod
    def _extract_excerpt(chunk: dict[str, Any]) -> str:
        for key in ("content", "text", "chunk"):
            value = chunk.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()[:500]
        return ""

    @staticmethod
    def _extract_score(chunk: dict[str, Any], rank: int) -> float:
        for key in ("score", "similarity", "distance"):
            value = chunk.get(key)
            if isinstance(value, int | float):
                score = float(value)
                if key == "distance":
                    score = 1.0 - score
                return round(min(1.0, max(0.0, score)), 2)
        return round(max(0.1, 1.0 - rank * 0.15), 2)

    async def _aindex_markdown(self, *, clear_storage: bool) -> IndexResult:
        if clear_storage:
            self._clear_storage_dir()

        self.settings.storage_dir.mkdir(parents=True, exist_ok=True)
        parsed_documents, skipped_documents = self._load_parsed_markdown_documents()
        documents = [parsed.body_text for parsed in parsed_documents]
        relative_paths = [parsed.relative_path for parsed in parsed_documents]

        if not documents:
            return IndexResult(
                status="no_documents",
                indexed_documents=0,
                skipped_documents=skipped_documents,
                storage_dir=self.settings.storage_dir,
                message="No Markdown documents found to index.",
            )

        duplicate_groups = self._detect_duplicates(parsed_documents)
        manifest_entries = self._build_manifest_entries(parsed_documents, duplicate_groups)
        metadata_warnings = [warning for parsed in parsed_documents for warning in parsed.warnings]

        if self._should_use_local_fallback():
            self._write_local_fallback_index(documents, relative_paths)
            self._write_manifest(manifest_entries, duplicate_groups)
            self._write_local_graph_index(parsed_documents)
            return IndexResult(
                status="indexed",
                indexed_documents=len(documents),
                skipped_documents=skipped_documents,
                storage_dir=self.settings.storage_dir,
                message=f"Indexed {len(documents)} Markdown document(s).",
                metadata_warnings=metadata_warnings,
                duplicate_groups=duplicate_groups,
                manifest_path=self._manifest_path(),
            )

        rag = self._build_lightrag()
        await rag.ainsert(documents, file_paths=relative_paths)
        self._write_manifest(manifest_entries, duplicate_groups)
        self._write_local_graph_index(parsed_documents)

        return IndexResult(
            status="indexed",
            indexed_documents=len(documents),
            skipped_documents=skipped_documents,
            storage_dir=self.settings.storage_dir,
            message=f"Indexed {len(documents)} Markdown document(s).",
            metadata_warnings=metadata_warnings,
            duplicate_groups=duplicate_groups,
            manifest_path=self._manifest_path(),
        )

    def _discover_markdown_files(self) -> list[Path]:
        """Return recursively discovered Markdown files in deterministic order."""

        knowledge_dir = self.settings.knowledge_dir
        if not knowledge_dir.exists():
            return []
        return sorted(knowledge_dir.rglob("*.md"), key=lambda path: path.as_posix())

    def _load_markdown_documents(self) -> tuple[list[str], list[str], int]:
        parsed_documents, skipped_documents = self._load_parsed_markdown_documents()
        return (
            [parsed.body_text for parsed in parsed_documents],
            [parsed.relative_path for parsed in parsed_documents],
            skipped_documents,
        )

    def _load_parsed_markdown_documents(self) -> tuple[list[_ParsedMarkdownDocument], int]:
        documents: list[str] = []
        parsed_documents: list[_ParsedMarkdownDocument] = []
        skipped_documents = 0

        for path in self._discover_markdown_files():
            parsed = self._parse_markdown_document(path)
            if not parsed.body_text.strip():
                skipped_documents += 1
                continue

            documents.append(parsed.body_text)
            parsed_documents.append(parsed)

        return parsed_documents, skipped_documents

    def _manifest_path(self) -> Path:
        return self.settings.storage_dir / MANIFEST_FILENAME

    def _graph_index_path(self) -> Path:
        return self.settings.storage_dir / LOCAL_GRAPH_INDEX_FILENAME

    def _build_manifest_entries(
        self, parsed_documents: list[_ParsedMarkdownDocument], duplicate_groups: list[DuplicateGroup]
    ) -> list[ManifestEntry]:
        generated_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        group_ids_by_path: dict[str, list[str]] = {parsed.relative_path: [] for parsed in parsed_documents}
        for group in duplicate_groups:
            for path in group.paths:
                group_ids_by_path.setdefault(path, []).append(group.group_id)
        return [
            ManifestEntry(
                path=parsed.relative_path,
                content_hash=parsed.content_hash,
                body_hash=parsed.body_hash,
                metadata=parsed.metadata,
                indexed_at=generated_at,
                warnings=parsed.warnings,
                body_excerpt=parsed.body_excerpt,
                duplicate_group_ids=sorted(group_ids_by_path.get(parsed.relative_path, [])),
            )
            for parsed in parsed_documents
        ]

    def _write_manifest(self, entries: list[ManifestEntry], duplicate_groups: list[DuplicateGroup]) -> None:
        payload = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "entries": [entry.to_dict() for entry in entries],
            "duplicate_groups": [group.to_dict() for group in duplicate_groups],
        }
        self._manifest_path().write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _read_manifest(self) -> dict[str, Any] | None:
        if not self._manifest_path().exists():
            return None
        return json.loads(self._manifest_path().read_text(encoding="utf-8"))

    def _write_local_graph_index(self, parsed_documents: list[_ParsedMarkdownDocument]) -> None:
        generated_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        docs_by_slug: dict[str, _ParsedMarkdownDocument] = {}
        for parsed in parsed_documents:
            stem = Path(parsed.relative_path).stem.lower()
            docs_by_slug[stem] = parsed
            title = parsed.metadata.get("title")
            if title:
                docs_by_slug[self._slugify(title)] = parsed

        outgoing_by_path: dict[str, list[str]] = {}
        incoming_counts: dict[str, int] = {parsed.relative_path: 0 for parsed in parsed_documents}
        edges: list[dict[str, str]] = []
        for parsed in parsed_documents:
            links = self._extract_wikilinks(parsed.raw_content)
            outgoing_by_path[parsed.relative_path] = links
            for link in links:
                target = docs_by_slug.get(self._slugify(link))
                target_path = target.relative_path if target is not None else f"{self._slugify(link)}.md"
                if target is not None:
                    incoming_counts[target.relative_path] = incoming_counts.get(target.relative_path, 0) + 1
                edges.append({"source": parsed.relative_path, "target": target_path, "label": "wikilink"})

        documents = [
            self._graph_document_payload(
                parsed,
                outgoing_wikilinks=outgoing_by_path.get(parsed.relative_path, []),
                incoming_link_count=incoming_counts.get(parsed.relative_path, 0),
            )
            for parsed in parsed_documents
        ]
        payload = {
            "schema_version": 1,
            "generated_at": generated_at,
            "documents": documents,
            "edges": sorted(edges, key=lambda edge: (edge["source"], edge["target"])),
        }
        self._graph_index_path().write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _graph_document_payload(
        self,
        parsed: _ParsedMarkdownDocument,
        *,
        outgoing_wikilinks: list[str],
        incoming_link_count: int,
    ) -> dict[str, Any]:
        frontmatter = self._parse_frontmatter_values(parsed.raw_content)
        metadata = {**parsed.metadata}
        scalar = lambda key: self._first_value(frontmatter.get(key), metadata.get(key, ""))
        keywords = self._frontmatter_list(frontmatter, "keywords", "keywords_de", "keywords_en")
        aliases = self._frontmatter_list(frontmatter, "aliases")
        tags = self._frontmatter_list(frontmatter, "tags")
        related = self._frontmatter_list(frontmatter, "related")
        commands = self._extract_commands(parsed.body_text, frontmatter)
        headings = self._extract_headings(parsed.body_text)
        token_text = "\n".join(
            [
                parsed.relative_path,
                scalar("title"),
                scalar("type"),
                scalar("service"),
                scalar("system") or scalar("systeme"),
                scalar("component") or scalar("komponente"),
                *keywords,
                *aliases,
                *tags,
                *related,
                *headings,
                *commands,
                *outgoing_wikilinks,
            ]
        )
        return {
            "path": parsed.relative_path,
            "title": scalar("title") or Path(parsed.relative_path).stem.replace("-", " "),
            "type": scalar("type"),
            "service": scalar("service"),
            "system": scalar("system") or scalar("systeme"),
            "component": scalar("component") or scalar("komponente"),
            "keywords": keywords,
            "aliases": aliases,
            "tags": tags,
            "related": related,
            "headings": headings,
            "commands": commands,
            "outgoing_wikilinks": outgoing_wikilinks,
            "incoming_link_count": incoming_link_count,
            "search_tokens": sorted(self._tokenize(token_text)),
            "metadata": metadata,
            "excerpt": parsed.body_excerpt,
        }

    @staticmethod
    def _slugify(value: str) -> str:
        value = value.split("|", 1)[0].strip().lower()
        value = re.sub(r"\.md$", "", value)
        value = re.sub(r"[^\wÄÖÜäöüß]+", "-", value)
        return value.strip("-")

    @staticmethod
    def _first_value(value: object, fallback: str = "") -> str:
        if isinstance(value, list):
            return str(value[0]).strip() if value else fallback
        if isinstance(value, str):
            return value.strip()
        return fallback

    def _frontmatter_list(self, frontmatter: dict[str, object], *keys: str) -> list[str]:
        values: list[str] = []
        for key in keys:
            raw = frontmatter.get(key)
            if isinstance(raw, list):
                values.extend(str(item).strip() for item in raw if str(item).strip())
            elif isinstance(raw, str) and raw.strip():
                stripped = raw.strip()
                if stripped.startswith("[") and stripped.endswith("]"):
                    values.extend(part.strip().strip("'\"") for part in stripped[1:-1].split(",") if part.strip())
                else:
                    values.append(stripped)
        return sorted(dict.fromkeys(values))

    def _parse_frontmatter_values(self, content: str) -> dict[str, object]:
        if not content.startswith("---\n"):
            return {}
        lines = content.splitlines()
        closing_index: int | None = None
        for index, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                closing_index = index
                break
        if closing_index is None:
            return {}
        values: dict[str, object] = {}
        current_key: str | None = None
        for line in lines[1:closing_index]:
            stripped = line.strip()
            if stripped.startswith("-") and current_key:
                existing = values.setdefault(current_key, [])
                if isinstance(existing, list):
                    existing.append(stripped[1:].strip().strip("'\""))
                continue
            if ":" not in line:
                current_key = None
                continue
            key, value = line.split(":", 1)
            current_key = key.strip().lower()
            cleaned = value.strip().strip("'\"")
            values[current_key] = cleaned
            if cleaned == "":
                values[current_key] = []
        return values

    @staticmethod
    def _extract_headings(text: str) -> list[str]:
        headings = [match.group(1).strip() for match in re.finditer(r"^#{1,6}\s+(.+)$", text, re.MULTILINE)]
        return sorted(dict.fromkeys(headings))

    @staticmethod
    def _extract_wikilinks(text: str) -> list[str]:
        links = [match.group(1).split("|", 1)[0].strip() for match in re.finditer(r"\[\[([^\]]+)\]\]", text)]
        return sorted(dict.fromkeys(link for link in links if link))

    def _extract_commands(self, body_text: str, frontmatter: dict[str, object]) -> list[str]:
        commands = self._frontmatter_list(frontmatter, "splunk_queries")
        in_commands_section = False
        in_fence = False
        for line in body_text.splitlines():
            stripped = line.strip()
            if re.match(r"^#{1,6}\s+", stripped):
                in_commands_section = bool(re.search(r"commands?|befehle|kommandos", stripped, re.IGNORECASE))
                continue
            if not in_commands_section:
                continue
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence and stripped:
                commands.append(stripped)
            for inline in re.findall(r"`([^`]+)`", stripped):
                if inline.strip():
                    commands.append(inline.strip())
        return sorted(dict.fromkeys(commands))

    def _manifest_entries_by_path(self, manifest: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
        if manifest is None:
            return {}
        entries = manifest.get("entries", [])
        if not isinstance(entries, list):
            return {}
        by_path: dict[str, dict[str, Any]] = {}
        for entry in entries:
            if isinstance(entry, dict) and isinstance(entry.get("path"), str):
                by_path[entry["path"]] = entry
        return by_path

    def _validate_manifest_schema(self, manifest: dict[str, Any]) -> None:
        if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
            msg = "Manifest schema version is incompatible. Run `ood reindex` to rebuild the knowledge manifest."
            raise ValueError(msg)

    def _build_manifest_diff(
        self, parsed_documents: list[_ParsedMarkdownDocument], previous_entries: dict[str, dict[str, Any]]
    ) -> ManifestDiff:
        current_by_path = {parsed.relative_path: parsed for parsed in parsed_documents}
        new_paths: list[str] = []
        changed_paths: list[str] = []
        unchanged_paths: list[str] = []
        for path in sorted(current_by_path):
            previous = previous_entries.get(path)
            if previous is None:
                new_paths.append(path)
            elif previous.get("content_hash") == current_by_path[path].content_hash:
                unchanged_paths.append(path)
            else:
                changed_paths.append(path)
        deleted_paths = sorted(set(previous_entries) - set(current_by_path))
        skipped_paths = [
            path.relative_to(self.settings.knowledge_dir).as_posix()
            for path in self._discover_markdown_files()
            if not self._parse_markdown_document(path).body_text.strip()
        ]
        return ManifestDiff(new_paths, changed_paths, unchanged_paths, deleted_paths, skipped_paths)

    def _detect_duplicates(
        self, parsed_documents: list[_ParsedMarkdownDocument], touched_paths: set[str] | None = None
    ) -> list[DuplicateGroup]:
        groups: list[DuplicateGroup] = []
        by_body_hash: dict[str, list[_ParsedMarkdownDocument]] = {}
        for parsed in parsed_documents:
            by_body_hash.setdefault(parsed.body_hash, []).append(parsed)

        exact_paths: set[tuple[str, ...]] = set()
        for documents in by_body_hash.values():
            if len(documents) < 2:
                continue
            if touched_paths is not None and not any(parsed.relative_path in touched_paths for parsed in documents):
                continue
            paths = sorted(parsed.relative_path for parsed in documents)
            exact_paths.add(tuple(paths))
            groups.append(
                DuplicateGroup(
                    group_id=self._duplicate_group_id("exact", paths),
                    kind="exact",
                    canonical_path=self._select_canonical_duplicate(documents),
                    paths=paths,
                    score=1.0,
                )
            )

        seen_near: set[tuple[str, ...]] = set()
        for left_index, left in enumerate(parsed_documents):
            for right in parsed_documents[left_index + 1 :]:
                if left.body_hash == right.body_hash:
                    continue
                if touched_paths is not None and left.relative_path not in touched_paths and right.relative_path not in touched_paths:
                    continue
                score = self._jaccard_similarity(left.body_text, right.body_text)
                if score < 0.85:
                    continue
                paths = tuple(sorted([left.relative_path, right.relative_path]))
                if paths in seen_near or paths in exact_paths:
                    continue
                seen_near.add(paths)
                documents = [left, right]
                groups.append(
                    DuplicateGroup(
                        group_id=self._duplicate_group_id("near", list(paths)),
                        kind="near",
                        canonical_path=self._select_canonical_duplicate(documents),
                        paths=list(paths),
                        score=round(score, 2),
                    )
                )
        return sorted(groups, key=lambda group: (group.kind, group.paths, group.group_id))

    def _select_canonical_duplicate(self, documents: list[_ParsedMarkdownDocument]) -> str:
        def parse_date(value: str | None) -> date:
            if not value:
                return date.min
            try:
                return date.fromisoformat(value)
            except ValueError:
                return date.min

        return sorted(
            documents,
            key=lambda parsed: (
                parsed.metadata.get("status") == "active",
                parse_date(parsed.metadata.get("datum")),
                tuple(chr(255 - ord(char)) for char in parsed.relative_path),
            ),
            reverse=True,
        )[0].relative_path

    def _jaccard_similarity(self, left: str, right: str) -> float:
        left_tokens = self._tokenize(left)
        right_tokens = self._tokenize(right)
        if not left_tokens and not right_tokens:
            return 1.0
        if not left_tokens or not right_tokens:
            return 0.0
        return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)

    def _duplicate_group_id(self, kind: str, paths: list[str]) -> str:
        digest = self._sha256("\n".join([kind, *sorted(paths)]))[:12]
        return f"{kind}:{digest}"

    def _parse_markdown_document(self, path: Path) -> _ParsedMarkdownDocument:
        raw_content = path.read_text(encoding="utf-8")
        relative_path = path.relative_to(self.settings.knowledge_dir).as_posix()
        metadata, body_text = self._split_frontmatter(raw_content)
        normalized_body = self._normalize_body(body_text)
        return _ParsedMarkdownDocument(
            path=path,
            relative_path=relative_path,
            raw_content=raw_content,
            body_text=body_text.strip(),
            metadata=metadata,
            warnings=self._metadata_warnings(relative_path, metadata),
            content_hash=self._sha256(raw_content),
            body_hash=self._sha256(normalized_body),
            body_excerpt=body_text.strip()[:500],
        )

    def _split_frontmatter(self, content: str) -> tuple[dict[str, str], str]:
        if not content.startswith("---\n"):
            return {}, content

        lines = content.splitlines()
        closing_index: int | None = None
        for index, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                closing_index = index
                break
        if closing_index is None:
            return {}, content

        metadata: dict[str, str] = {}
        for line in lines[1:closing_index]:
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]
            if key:
                metadata[key] = value
        body = "\n".join(lines[closing_index + 1 :])
        return metadata, body

    def _metadata_warnings(self, relative_path: str, metadata: dict[str, str]) -> list[MetadataWarning]:
        warnings: list[MetadataWarning] = []
        for field_name in REQUIRED_METADATA_FIELDS:
            if not metadata.get(field_name):
                warnings.append(
                    MetadataWarning(path=relative_path, field=field_name, message=f"Missing required metadata field: {field_name}.")
                )
        status = metadata.get("status")
        if status and status not in VALID_STATUS_VALUES:
            warnings.append(
                MetadataWarning(
                    path=relative_path,
                    field="status",
                    message="Invalid status value. Expected one of: active, deprecated, draft.",
                )
            )
        return warnings

    @staticmethod
    def _sha256(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_body(text: str) -> str:
        return "\n".join(line.strip() for line in text.strip().splitlines() if line.strip())

    def _should_use_local_fallback(self) -> bool:
        return not self.settings.can_use_cloud_llm and LightRAG is None

    @property
    def _fallback_index_path(self) -> Path:
        return self.settings.storage_dir / LOCAL_VECTOR_INDEX_FILENAME

    def _write_local_fallback_index(self, documents: list[str], relative_paths: list[str]) -> None:
        vectors = self._encode_local_embeddings(documents)
        payload = {
            "documents": [
                {
                    "path": path,
                    "content": content,
                    "excerpt": content.strip()[:500],
                    "vector": [float(value) for value in vector],
                }
                for path, content, vector in zip(relative_paths, documents, vectors, strict=True)
            ]
        }
        self._fallback_index_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    def _encode_local_embeddings(self, texts: list[str]) -> list[list[float]]:
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(LOCAL_EMBEDDING_MODEL)
        encoded = model.encode(texts, normalize_embeddings=True)
        return [[float(value) for value in vector] for vector in encoded]

    def _query_local_fallback(self, query_text: str) -> list[SourceHit]:
        if not self._fallback_index_path.exists():
            return []

        try:
            payload = json.loads(self._fallback_index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        documents = payload.get("documents", [])
        if not isinstance(documents, list):
            return []

        valid_documents: list[tuple[str, str, str, list[float]]] = []
        for document in documents:
            if not isinstance(document, dict):
                continue
            path = document.get("path")
            content = document.get("content")
            vector = document.get("vector")
            if (
                not isinstance(path, str)
                or not isinstance(content, str)
                or not content.strip()
                or not self._is_numeric_vector(vector)
            ):
                continue
            excerpt = document.get("excerpt")
            if not isinstance(excerpt, str) or not excerpt.strip():
                excerpt = content.strip()[:500]
            valid_documents.append((path, content, excerpt.strip()[:500], vector))

        if not valid_documents:
            return []

        query_vectors = self._encode_local_embeddings([query_text])
        if not query_vectors:
            return []
        query_vector = query_vectors[0]
        query_tokens = self._tokenize(query_text)
        graph_index = self._read_local_graph_index()
        scored: list[tuple[SourceHit, SourceScoreBreakdown]] = []
        for path, content, excerpt, vector in valid_documents:
            semantic_score = min(1.0, max(0.0, self._cosine_similarity(query_vector, vector)))
            lexical_score, lexical_matches, exact_match = self._score_lexical_match(query_tokens, content)
            graph_doc = graph_index.get("documents_by_path", {}).get(path) if graph_index else None
            metadata_score = 0.0
            metadata_matches: list[str] = []
            graph_score = 0.0
            graph_matches: list[str] = []
            if isinstance(graph_doc, dict) and graph_index is not None:
                metadata_score, metadata_matches = self._score_metadata_match(query_tokens, graph_doc)
                graph_score, graph_matches = self._score_graph_match(query_tokens, graph_doc, graph_index)
                weights = {
                    "semantic": HYBRID_GRAPH_SEMANTIC_WEIGHT,
                    "lexical": HYBRID_GRAPH_LEXICAL_WEIGHT,
                    "metadata": HYBRID_GRAPH_METADATA_WEIGHT,
                    "graph": HYBRID_GRAPH_GRAPH_WEIGHT,
                    "exact_token_boost": HYBRID_EXACT_TOKEN_BOOST if exact_match else 0.0,
                }
                combined_score = min(
                    1.0,
                    semantic_score * HYBRID_GRAPH_SEMANTIC_WEIGHT
                    + lexical_score * HYBRID_GRAPH_LEXICAL_WEIGHT
                    + metadata_score * HYBRID_GRAPH_METADATA_WEIGHT
                    + graph_score * HYBRID_GRAPH_GRAPH_WEIGHT
                    + (HYBRID_EXACT_TOKEN_BOOST if exact_match else 0.0),
                )
            else:
                weights = {
                    "semantic": HYBRID_SEMANTIC_WEIGHT,
                    "lexical": HYBRID_LEXICAL_WEIGHT,
                    "exact_token_boost": HYBRID_EXACT_TOKEN_BOOST if exact_match else 0.0,
                }
                combined_score = min(
                    1.0,
                    semantic_score * HYBRID_SEMANTIC_WEIGHT
                    + lexical_score * HYBRID_LEXICAL_WEIGHT
                    + (HYBRID_EXACT_TOKEN_BOOST if exact_match else 0.0),
                )
            breakdown = SourceScoreBreakdown(
                path=path,
                semantic_score=round(semantic_score, 4),
                lexical_score=round(lexical_score, 4),
                combined_score=round(combined_score, 4),
                lexical_matches=lexical_matches,
                weights=weights,
                metadata_score=round(metadata_score, 4),
                graph_score=round(graph_score, 4),
                final_score=round(combined_score, 4),
                metadata_matches=metadata_matches,
                graph_matches=graph_matches,
            )
            score_details = breakdown.to_dict()
            scored.append((SourceHit(path=path, score=round(combined_score, 2), excerpt=excerpt, score_details=score_details), breakdown))
        ranked = sorted(scored, key=lambda item: item[0].score, reverse=True)[:QUERY_SOURCE_LIMIT]
        self._last_retrieval_diagnostics = self._local_retrieval_diagnostics([breakdown for _source, breakdown in ranked], graph_index=graph_index)
        return [source for source, _breakdown in ranked]

    def _score_lexical_match(self, query_tokens: set[str], content: str) -> tuple[float, list[str], bool]:
        if not query_tokens:
            return 0.0, [], False
        content_tokens = self._tokenize(content)
        matches = sorted(query_tokens & content_tokens)
        if not matches:
            return 0.0, [], False
        coverage = len(matches) / len(query_tokens)
        exact_operational_matches = [token for token in matches if self._is_operational_token(token)]
        exact_bonus = min(0.5, len(exact_operational_matches) * 0.25)
        lexical_score = min(1.0, coverage + exact_bonus)
        return lexical_score, matches, bool(exact_operational_matches)

    @staticmethod
    def _is_operational_token(token: str) -> bool:
        return bool(re.search(r"\d", token) or "-" in token or len(token) <= 3)

    def _read_local_graph_index(self) -> dict[str, Any] | None:
        if not self._graph_index_path().exists():
            return None
        try:
            payload = json.loads(self._graph_index_path().read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        documents = payload.get("documents")
        edges = payload.get("edges", [])
        if not isinstance(documents, list):
            return None
        documents_by_path = {doc.get("path"): doc for doc in documents if isinstance(doc, dict) and isinstance(doc.get("path"), str)}
        incoming_by_target: dict[str, list[str]] = {}
        outgoing_by_source: dict[str, list[str]] = {}
        if isinstance(edges, list):
            for edge in edges:
                if not isinstance(edge, dict):
                    continue
                source = edge.get("source")
                target = edge.get("target")
                if isinstance(source, str) and isinstance(target, str):
                    incoming_by_target.setdefault(target, []).append(source)
                    outgoing_by_source.setdefault(source, []).append(target)
        return {
            "payload": payload,
            "documents": documents,
            "documents_by_path": documents_by_path,
            "incoming_by_target": incoming_by_target,
            "outgoing_by_source": outgoing_by_source,
            "edge_count": sum(len(targets) for targets in outgoing_by_source.values()),
        }

    def _score_metadata_match(self, query_tokens: set[str], graph_doc: dict[str, Any]) -> tuple[float, list[str]]:
        weighted_fields: list[tuple[str, float, str]] = [
            ("title", 0.16, "title"),
            ("type", 0.08, "type"),
            ("service", 0.16, "service"),
            ("system", 0.14, "system"),
            ("component", 0.14, "component"),
        ]
        score = 0.0
        matches: list[str] = []
        for field, weight, label in weighted_fields:
            value = graph_doc.get(field)
            if isinstance(value, str) and query_tokens & self._tokenize(value):
                score += weight
                matches.append(f"{label}:{value}")
        list_fields: list[tuple[str, float, str]] = [
            ("keywords", 0.22, "keyword"),
            ("aliases", 0.08, "alias"),
            ("tags", 0.06, "tag"),
            ("headings", 0.08, "heading"),
            ("commands", 0.08, "command"),
        ]
        for field, weight, label in list_fields:
            field_matches = self._list_field_matches(query_tokens, graph_doc.get(field), label)
            if field_matches:
                score += min(weight, 0.06 * len(field_matches) if field != "keywords" else weight)
                matches.extend(field_matches)
        search_tokens = graph_doc.get("search_tokens")
        if isinstance(search_tokens, list):
            overlap = sorted(query_tokens & {str(token).lower() for token in search_tokens})
            if overlap:
                score += min(0.18, len(overlap) / max(1, len(query_tokens)) * 0.18)
                matches.extend(f"token:{token}" for token in overlap)
        return round(min(1.0, score), 4), sorted(dict.fromkeys(matches))

    def _score_graph_match(self, query_tokens: set[str], graph_doc: dict[str, Any], graph_index: dict[str, Any]) -> tuple[float, list[str]]:
        path = graph_doc.get("path")
        if not isinstance(path, str):
            return 0.0, []
        docs_by_path = graph_index.get("documents_by_path", {})
        score = 0.0
        matches: list[str] = []
        outgoing = graph_index.get("outgoing_by_source", {}).get(path, [])
        for target in outgoing:
            target_doc = docs_by_path.get(target)
            target_text = target
            if isinstance(target_doc, dict):
                target_text = " ".join(
                    str(value)
                    for value in [target_doc.get("title"), *(target_doc.get("keywords") or []), *(target_doc.get("search_tokens") or [])]
                    if value
                )
            if query_tokens & self._tokenize(target_text):
                score += 0.3
            else:
                score += 0.12
            matches.append(f"link:{target}")
        incoming = graph_index.get("incoming_by_target", {}).get(path, [])
        if incoming:
            score += min(0.4, 0.18 * len(incoming))
            matches.extend(f"incoming_link:{source}" for source in incoming)
        incoming_count = graph_doc.get("incoming_link_count")
        if isinstance(incoming_count, int) and incoming_count > 0:
            score += min(0.2, incoming_count * 0.08)
        return round(min(1.0, score), 4), sorted(dict.fromkeys(matches))

    def _list_field_matches(self, query_tokens: set[str], values: object, label: str) -> list[str]:
        if not isinstance(values, list):
            return []
        matches: list[str] = []
        for value in values:
            text = str(value)
            if query_tokens & self._tokenize(text):
                matches.append(f"{label}:{text}")
        return matches

    def _local_retrieval_diagnostics(self, score_components: list[SourceScoreBreakdown], graph_index: dict[str, Any] | None = None) -> RetrievalDiagnostics:
        if graph_index is None:
            return RetrievalDiagnostics(
                backend="local_vector_index",
                strategy="hybrid_semantic_lexical",
                score_components=score_components,
                graph_retrieval={
                    "status": "deferred",
                    "artifact_path": str(self._graph_index_path()),
                    "reason": "Local graph artifact is missing or malformed; using semantic+lexical fallback.",
                    "replacement": "hybrid semantic+lexical retrieval",
                },
                notes=["Local retrieval combines semantic cosine similarity with lexical exact-token signals; graph artifact was not available."],
            )
        return RetrievalDiagnostics(
            backend="local_vector_graph_index",
            strategy="hybrid_semantic_lexical_metadata_graph",
            score_components=score_components,
            graph_retrieval={
                "status": "active",
                "artifact_path": str(self._graph_index_path()),
                "document_count": len(graph_index.get("documents", [])),
                "edge_count": graph_index.get("edge_count", 0),
                "replacement": "active local graph/metadata fusion",
            },
            notes=["Local retrieval fuses semantic vectors, lexical exact tokens, metadata fields, and Wikilink graph signals."],
        )

    def _lightrag_retrieval_diagnostics(self, *, strategy: str, sources: list[SourceHit]) -> RetrievalDiagnostics:
        return RetrievalDiagnostics(
            backend="lightrag",
            strategy=strategy,
            score_components=[
                SourceScoreBreakdown(
                    path=source.path,
                    semantic_score=source.score,
                    lexical_score=0.0,
                    combined_score=source.score,
                    lexical_matches=[],
                    weights={"backend_score": 1.0},
                )
                for source in sources
            ],
            graph_retrieval=self._graph_retrieval_deferred(),
            notes=["LightRAG source scores are normalized into the OOD source contract."],
        )

    @staticmethod
    def _graph_retrieval_deferred() -> dict[str, Any]:
        return {
            "status": "deferred",
            "reason": "Local CLI artifacts currently persist vectors and source content, but no deterministic graph entity or relationship artifact.",
            "risk": "Graph-only relationships may be missed until a local graph artifact is available.",
            "replacement": "hybrid semantic+lexical retrieval",
            "activation_criteria": [
                "local graph artifact persists entities and relationships",
                "deterministic tests prove graph retrieval lifts relationship-only matches",
                "privacy-safe query path works without Cloud LLM approval",
            ],
        }

    def _count_local_vector_documents(self) -> int:
        if not self._fallback_index_path.exists():
            return 0
        try:
            payload = json.loads(self._fallback_index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return 0
        documents = payload.get("documents", [])
        if not isinstance(documents, list):
            return 0
        return sum(1 for document in documents if isinstance(document, dict))

    @staticmethod
    def _is_numeric_vector(value: object) -> bool:
        return isinstance(value, list) and all(isinstance(item, int | float) for item in value)

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        left_array = np.array(left, dtype=float)
        right_array = np.array(right, dtype=float)
        denominator = np.linalg.norm(left_array) * np.linalg.norm(right_array)
        if denominator == 0:
            return 0.0
        return float(np.dot(left_array, right_array) / denominator)

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return {token.lower() for token in re.findall(r"[\wÄÖÜäöüß]+(?:-[\wÄÖÜäöüß]+)*", text) if len(token) > 1}

    def _build_lightrag(self) -> Any:
        global LightRAG

        if LightRAG is None:
            from lightrag import LightRAG as ImportedLightRAG

            LightRAG = ImportedLightRAG

        return LightRAG(
            working_dir=str(self.settings.storage_dir),
            embedding_func=self._build_embedding_func(),
            llm_model_func=self._build_llm_model_func(),
        )

    def _build_embedding_func(self) -> Any:
        from lightrag.utils import EmbeddingFunc
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(LOCAL_EMBEDDING_MODEL)

        async def _embed(texts: list[str]) -> np.ndarray:
            return model.encode(texts, normalize_embeddings=True)

        return EmbeddingFunc(
            embedding_dim=LOCAL_EMBEDDING_DIM,
            max_token_size=MAX_EMBEDDING_TOKENS,
            func=_embed,
        )

    @staticmethod
    async def _noop_llm_model_func(prompt: str, **_: object) -> str:
        return ""

    def _build_llm_model_func(self) -> Callable[..., Awaitable[str]]:
        if not self.settings.can_use_cloud_llm:
            return self._noop_llm_model_func

        if self.settings.llm_provider not in (None, "openai", "openai-compatible"):
            return self._noop_llm_model_func

        api_key = self.settings.llm_api_key.get_secret_value()
        model = self.settings.llm_model or "gpt-4o-mini"

        async def _llm_model_func(
            prompt: str,
            system_prompt: str | None = None,
            history_messages: list[dict[str, Any]] | None = None,
            **kwargs: Any,
        ) -> str:
            global openai_complete_if_cache

            if openai_complete_if_cache is None:
                from lightrag.llm.openai import openai_complete_if_cache as imported_complete

                openai_complete_if_cache = imported_complete
            return await openai_complete_if_cache(
                model,
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages or [],
                api_key=api_key,
                **kwargs,
            )

        return _llm_model_func

    def reindex_markdown(self) -> IndexResult:
        """Clear only configured storage and rebuild Markdown index."""

        return asyncio.run(self._aindex_markdown(clear_storage=True))

    def _clear_storage_dir(self) -> None:
        storage_dir = self.settings.storage_dir
        forbidden = {
            self.settings.data_dir.resolve(),
            self.settings.knowledge_dir.resolve(),
            Path(".env").resolve(),
        }
        if storage_dir.resolve() in forbidden:
            msg = "Refusing to clear unsafe storage directory."
            raise ValueError(msg)

        if not storage_dir.exists():
            storage_dir.mkdir(parents=True, exist_ok=True)
            return

        for child in storage_dir.iterdir():
            if child.is_file() or child.is_symlink():
                child.unlink()
            elif child.is_dir():
                shutil.rmtree(child)

        storage_dir.mkdir(parents=True, exist_ok=True)


__all__ = [
    "LOCAL_EMBEDDING_DIM",
    "LOCAL_EMBEDDING_MODEL",
    "LOCAL_GRAPH_INDEX_FILENAME",
    "LOCAL_VECTOR_INDEX_FILENAME",
    "MANIFEST_FILENAME",
    "MANIFEST_SCHEMA_VERSION",
    "MAX_EMBEDDING_TOKENS",
    "REQUIRED_METADATA_FIELDS",
    "RagEngine",
    "VALID_STATUS_VALUES",
]
