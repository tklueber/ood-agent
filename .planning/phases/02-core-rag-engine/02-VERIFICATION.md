---
phase: 02-core-rag-engine
verified: 2026-05-01T13:27:30Z
status: passed
score: 14/14 must-haves verified
gaps: []
human_verification: []
---

# Phase 2: Core RAG Engine Verification Report

**Phase Goal:** User can index Markdown files and query them with semantic search  
**Verified:** 2026-05-01T13:27:30Z  
**Status:** passed  
**Re-verification:** No — initial verification

## Goal Achievement

Phase 2 goal is achieved. The actual codebase contains a Typer CLI wired to `RagEngine`, service logic for indexing/reindexing Markdown, query result contracts with source attribution/relevance/confidence, LightRAG integration for supported credentialed runtime paths, and a documented privacy-safe retrieval-only fallback when no Cloud LLM credentials are configured.

### Observable Truths

| # | Truth | Status | Evidence |
| --- | --- | --- | --- |
| 1 | User-facing index and query behavior is backed by LightRAG dependencies instead of custom retrieval code where runtime/credentials support it. | ✓ VERIFIED | `pyproject.toml` includes `lightrag-hku==1.4.15`; `src/ood/rag.py` builds `LightRAG(working_dir=..., embedding_func=..., llm_model_func=...)`; query uses `aquery_data` and `QueryParam`. |
| 2 | When Cloud LLM credentials are configured, users can run LLM-backed query generation without a missing OpenAI-compatible runtime dependency. | ✓ VERIFIED | `openai==2.33.0` is installed; import smoke command printed `rag-deps-ok`; `_build_llm_model_func()` imports `openai_complete_if_cache`. |
| 3 | CLI JSON output exposes stable source, score, confidence, and status fields without leaking LightRAG internals. | ✓ VERIFIED | `QueryResult.to_dict()` returns `query`, `answer`, `confidence`, `sources`, `llm_used`, `status`; CLI emits `json.dumps(result.to_dict())`. |
| 4 | User can run `ood index` service logic over recursive Markdown files. | ✓ VERIFIED | `RagEngine.index_markdown()` discovers `knowledge_dir.rglob("*.md")`, passes `file_paths=relative_paths`, and CLI smoke indexed one Markdown file successfully. |
| 5 | Missing or empty knowledge directories are successful zero-document no-ops. | ✓ VERIFIED | `_discover_markdown_files()` returns `[]` for missing dirs; `_aindex_markdown()` returns `IndexResult(status="no_documents")`; focused tests pass. |
| 6 | Clean rebuild clears only the configured storage directory before indexing. | ✓ VERIFIED | `reindex_markdown()` calls `_aindex_markdown(clear_storage=True)`; `_clear_storage_dir()` removes only children of `settings.storage_dir`; tests verify sibling/knowledge files are preserved. |
| 7 | User can query an existing index with semantic/retrieval search. | ✓ VERIFIED | `RagEngine.query()` checks index existence, uses LightRAG `aquery_data` when available and a documented local fallback without credentials; CLI smoke query returned sources. |
| 8 | Query results include relative source paths, scores, and excerpts. | ✓ VERIFIED | `_normalize_sources()` creates `SourceHit(path=..., score=..., excerpt=...)`; `_normalize_source_path()` strips paths relative to `knowledge_dir`; model/CLI tests pass. |
| 9 | Missing LLM credentials return retrieval-only results with `answer=null` and `llm_used=false`. | ✓ VERIFIED | No-credential path returns `QueryResult(answer=None, llm_used=False)`; README documents no Cloud LLM calls without credentials; smoke JSON showed retrieval-only shape. |
| 10 | Query before index exists fails with instruction to run `ood index` first. | ✓ VERIFIED | `_ensure_index_exists()` raises `IndexMissingError("No index found. Run `ood index` first.")`; CLI catches it and exits code 1; tests pass. |
| 11 | User can run `ood index` to build the initial knowledge base. | ✓ VERIFIED | CLI `index` calls `RagEngine(settings).index_markdown()` and smoke command succeeded. |
| 12 | User can run `ood reindex` to rebuild from scratch. | ✓ VERIFIED | CLI `reindex` calls `RagEngine(settings).reindex_markdown()` and service tests cover rebuild behavior. |
| 13 | User can run `ood query <text>` and receive answer/confidence/source output. | ✓ VERIFIED | CLI `query` calls `RagEngine(settings).query(ticket_text)`; human and JSON output tests verify confidence, rationale, sources, scores, excerpts. |
| 14 | `ood query --json` emits stable automation fields: query, answer, confidence, sources, llm_used, status. | ✓ VERIFIED | `tests/test_cli.py::test_query_json_output_matches_phase_2_contract` passes; CLI smoke parsed these fields. |

**Score:** 14/14 truths verified

### Phase Success Criteria

| Criterion | Status | Evidence |
| --- | --- | --- |
| User can run `index` command to build knowledge base from `knowledge/` directory | ✓ VERIFIED | CLI is wired to `RagEngine.index_markdown()`; recursive Markdown indexing implemented; CLI smoke passed. |
| User can run `query <text>` and receive relevant results with source attribution | ✓ VERIFIED | Query returns `SourceHit` entries; fallback smoke returned `runbook.md` for matching query. |
| Query results include relevance scores for each source | ✓ VERIFIED | `SourceHit.score`; normalization clamps scores to `0.0..1.0`; JSON smoke included score. |
| Query results include confidence scoring for generated answers/retrieval output | ✓ VERIFIED | `ConfidenceScore` and `_score_confidence()` used for all query paths. |
| System uses LightRAG for dual-level graph + vector retrieval where credentials/runtime support it, with documented/privacy-safe fallback behavior when no Cloud LLM credentials are configured | ✓ VERIFIED | LightRAG dependency/import works; credentialed path uses `QueryParam(mode="mix")` and LLM wrapper; no-credential fallback is documented in README and avoids Cloud LLM calls. |

### Required Artifacts

| Artifact | Expected | Status | Details |
| --- | --- | --- | --- |
| `pyproject.toml` | LightRAG, embeddings, OpenAI-compatible dependency stack | ✓ VERIFIED | Contains `lightrag-hku==1.4.15`, `sentence-transformers==5.4.1`, `openai==2.33.0`, `numpy`; import smoke passed. |
| `src/ood/models.py` | Stable `IndexResult`, `SourceHit`, `ConfidenceScore`, `QueryResult`, `IndexMissingError` contracts | ✓ VERIFIED | Dataclasses and `to_dict()` contracts exist with tests. |
| `src/ood/rag.py` | Markdown discovery, indexing/reindexing, LightRAG adapter, query/source normalization, confidence scoring | ✓ VERIFIED | Substantive implementation present; focused tests and CLI smoke pass. |
| `src/ood/cli.py` | Typer integration for index, query, reindex | ✓ VERIFIED | Commands instantiate `RagEngine(settings)` and emit Phase 2 JSON/human contracts. |
| `tests/test_models.py` | Model serialization coverage | ✓ VERIFIED | Included in focused test run. |
| `tests/test_rag.py` | Service indexing/query/reindex coverage | ✓ VERIFIED | Included in focused test run. |
| `tests/test_cli.py` | CLI contract coverage | ✓ VERIFIED | Included in focused test run. |
| `README.md` | Core RAG usage and fallback documentation | ✓ VERIFIED | Contains `## Core RAG usage`, command examples, and optional Cloud LLM/fallback guidance. |

### Key Link Verification

| From | To | Via | Status | Details |
| --- | --- | --- | --- | --- |
| `src/ood/cli.py` | `src/ood/rag.py` | `RagEngine(settings)` service calls | ✓ VERIFIED | `index`, `query`, and `reindex` call the service. |
| `src/ood/cli.py` | `QueryResult.to_dict` | JSON output | ✓ VERIFIED | `_emit_query_result()` emits `json.dumps(result.to_dict())`. |
| `src/ood/rag.py` | `Settings.knowledge_dir` | Recursive Markdown discovery | ✓ VERIFIED | `knowledge_dir = self.settings.knowledge_dir`; `knowledge_dir.rglob("*.md")`. |
| `src/ood/rag.py` | `Settings.storage_dir` | LightRAG `working_dir` and storage checks | ✓ VERIFIED | `working_dir=str(self.settings.storage_dir)` and storage marker checks. |
| `src/ood/rag.py` | `LightRAG.aquery_data` | `QueryParam(mode=...)` | ✓ VERIFIED | `_aquery()` calls `await rag.aquery_data(query_text, query_param)` with `naive` or `mix`. |
| `src/ood/rag.py` | `QueryResult.sources` | Chunk normalization to `SourceHit` | ✓ VERIFIED | `_normalize_sources()` builds sorted `SourceHit` list and passes it into `QueryResult`. |

Note: `gsd-tools verify key-links` produced false negatives for some links because it expected target names to be referenced literally from the source file; manual code verification confirmed the planned patterns exist.

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| --- | --- | --- | --- | --- |
| `src/ood/cli.py` | `result` | `RagEngine(settings).index_markdown()` / `.query()` / `.reindex_markdown()` | Yes | ✓ FLOWING |
| `src/ood/rag.py` | `documents`, `relative_paths` | Recursive reads from `settings.knowledge_dir` Markdown files | Yes | ✓ FLOWING |
| `src/ood/rag.py` | `sources` | LightRAG `aquery_data()` chunks or local fallback index | Yes | ✓ FLOWING |
| `src/ood/rag.py` | `confidence` | `_score_confidence(sources, llm_used)` | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| --- | --- | --- | --- |
| Phase test suite passes | `uv run pytest tests/test_models.py tests/test_rag.py tests/test_cli.py -q` | `27 passed in 0.42s` | ✓ PASS |
| Lockfile is current | `uv lock --check` | `Resolved 125 packages in 4ms` | ✓ PASS |
| RAG dependencies import | `uv run python -c "import lightrag, sentence_transformers, numpy, openai; from lightrag.llm.openai import openai_complete_if_cache; print('rag-deps-ok')"` | `rag-deps-ok` | ✓ PASS |
| CLI index/query JSON smoke | temp Markdown fixture with `uv run ood index --json ...` and `uv run ood query ... --json` | `cli-smoke-ok` | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| --- | --- | --- | --- | --- |
| RAG-01 | 02-02, 02-04 | System can index Markdown files from knowledge/ directory | ✓ SATISFIED | Recursive Markdown discovery, indexing service, and CLI command verified. |
| RAG-02 | 02-03, 02-04 | System supports semantic search over indexed tickets | ✓ SATISFIED | Query service exists; LightRAG query path uses `aquery_data`; fallback query documented for no credentials. |
| RAG-03 | 02-01, 02-03, 02-04 | Query results include source attribution with relevance scores | ✓ SATISFIED | `SourceHit(path, score, excerpt)` in model/service/CLI JSON. |
| RAG-04 | 02-01, 02-03, 02-04 | System provides confidence scoring for generated answers | ✓ SATISFIED | `ConfidenceScore`; `_score_confidence()` applied to query results. |
| RAG-05 | 02-01, 02-02, 02-03, 02-04 | System uses LightRAG for dual-level graph + vector retrieval | ✓ SATISFIED | Dependency present; LightRAG adapter builds `LightRAG`; credentialed query uses `mode="mix"`; fallback documented when credentials absent. |
| INF-01 | 02-02, 02-04 | CLI provides `index` command to build initial knowledge base | ✓ SATISFIED | `index` command calls `RagEngine.index_markdown()` and smoke passed. |
| INF-03 | 02-03, 02-04 | CLI provides `query` command for ticket analysis | ✓ SATISFIED | `query` command calls `RagEngine.query()` and emits JSON/human contracts. |
| INF-04 | 02-02, 02-04 | CLI provides `reindex` command to rebuild from scratch | ✓ SATISFIED | `reindex` command calls `RagEngine.reindex_markdown()`; safe rebuild tests pass. |

All Phase 2 requirement IDs from the prompt and PLAN frontmatter are accounted for. No additional Phase 2 IDs in `.planning/REQUIREMENTS.md` were orphaned.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| --- | --- | --- | --- | --- |
| `src/ood/cli.py` | 70 | `_emit_stub` remains for future `update` command | ℹ️ Info | Not Phase 2 blocker; `index`, `query`, and `reindex` no longer use stub output. |
| `src/ood/rag.py` | 124, 231, 267, 272 | `return []` empty-result branches | ℹ️ Info | Legitimate no-data branches, not placeholders; populated paths exist via LightRAG/fallback. |

### Human Verification Required

None. External real-credential LLM behavior was not invoked, but the code path is covered with monkeypatched tests and dependency import verification; no human-only UI or visual checks are part of this phase.

### Gaps Summary

No blocking gaps found. Phase 2 goal and all requested success criteria are verified against the codebase.

---

_Verified: 2026-05-01T13:27:30Z_  
_Verifier: the agent (gsd-verifier)_
