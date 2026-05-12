---
phase: 02-core-rag-engine
plan: 02
subsystem: rag-service
tags: [python, lightrag, markdown, indexing, reindex, testing]

requires:
  - phase: 02-core-rag-engine
    provides: LightRAG runtime dependencies and stable IndexResult model contracts
provides:
  - Recursive Markdown discovery and indexing through RagEngine.index_markdown()
  - Safe no-document indexing behavior for missing or empty knowledge directories
  - Credential-aware LightRAG LLM adapter selection with no-op fallback when no API key is configured
  - Clean reindex behavior scoped to Settings.storage_dir
affects: [02-core-rag-engine, cli-index, cli-reindex, rag-query]

tech-stack:
  added: []
  patterns: [service-layer LightRAG adapter, deterministic relative source paths, storage-scoped destructive cleanup]

key-files:
  created: [src/ood/rag.py, tests/test_rag.py]
  modified: []

key-decisions:
  - "Keep LightRAG construction behind RagEngine so CLI and future query logic do not depend on storage internals."
  - "Use a no-op LLM model function whenever credentials are absent so local indexing never sends content to a Cloud LLM."
  - "Scope clean rebuild deletion to children of Settings.storage_dir and preserve knowledge_dir plus sibling data files."

patterns-established:
  - "Markdown files are sorted by POSIX path and passed to LightRAG with relative file_paths for stable source identity."
  - "index_markdown() and reindex_markdown() share _aindex_markdown(), with only reindex enabling storage cleanup."

requirements-completed: [RAG-01, RAG-05, INF-01, INF-04]

duration: 3min 24s
completed: 2026-05-01
---

# Phase 02 Plan 02: Markdown Indexing and Clean Reindex Service Summary

**RagEngine service that recursively indexes Markdown into LightRAG storage with credential-safe LLM fallback and storage-scoped clean rebuilds**

## Performance

- **Duration:** 3min 24s
- **Started:** 2026-05-01T12:57:02Z
- **Completed:** 2026-05-01T13:00:26Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `RagEngine.index_markdown()` to discover recursive non-empty `*.md` files, accept plain Markdown, skip empty files, and pass relative paths into LightRAG.
- Added successful no-op behavior for missing or empty knowledge directories while still creating the configured storage directory.
- Added credential-aware LLM adapter selection: no credentials use the no-op fallback; configured OpenAI/OpenAI-compatible credentials use `openai_complete_if_cache` without exposing secrets.
- Added `RagEngine.reindex_markdown()` and storage cleanup that deletes only children of `settings.storage_dir` before rebuilding.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Implement Markdown discovery and no-op indexing** - `44df4af` (test)
2. **Task 1 GREEN: Implement Markdown discovery and no-op indexing** - `8c80a8b` (feat)
3. **Task 2: Implement clean reindex scoped to storage_dir** - `0869d61` (test)

_Note: Task 1 followed TDD with separate failing-test and implementation commits. The shared `_aindex_markdown()` implementation in `8c80a8b` also included the planned reindex path; Task 2 then committed the dedicated safety tests that lock the behavior._

## Files Created/Modified

- `src/ood/rag.py` - Adds `RagEngine`, Markdown discovery/loading, LightRAG construction, embedding/LLM function builders, no-op indexing results, and storage-scoped clean reindex cleanup.
- `tests/test_rag.py` - Verifies recursive plain Markdown indexing, no-document no-ops, LLM fallback selection, credential-backed LLM adapter selection, clean reindex scope, and normal index storage preservation.

## Decisions Made

- Kept all LightRAG-specific construction in `RagEngine` so future CLI and query plans can use OOD-owned service methods and stable result models.
- Preserved the privacy constraint by returning `_noop_llm_model_func` unless `Settings.has_llm_credentials` is true and the provider is OpenAI-compatible.
- Implemented clean reindex without shell commands and without removing parent directories, `knowledge_dir`, `data_dir`, or `.env`.

## Deviations from Plan

None - plan scope executed as written.

## Issues Encountered

- Task 2 implementation landed in the shared Task 1 service commit because `reindex_markdown()` is a thin wrapper around the same `_aindex_markdown()` flow. Dedicated Task 2 verification was still added and committed separately.
- The acceptance-string check initially used `python`, but the environment exposes Python through `uv run python`; the verification was rerun successfully with `uv run python`.
- No authentication gates or external-service setup were required.
- No secrets were configured, logged, or committed.

## Known Stubs

None - no placeholder or UI-facing empty-data stubs were introduced in the files created by this plan.

## User Setup Required

None - no external service configuration required for local no-credential indexing.

## Next Phase Readiness

- Plan 02-03 can build query/retrieval behavior on top of the same `RagEngine` service boundary and configured LightRAG storage.
- Plan 02-04 can wire CLI `index` and `reindex` commands to `RagEngine.index_markdown()` and `RagEngine.reindex_markdown()`.

## Self-Check: PASSED

- Found created implementation file: `src/ood/rag.py`.
- Found created test file: `tests/test_rag.py`.
- Found summary file: `.planning/phases/02-core-rag-engine/02-02-SUMMARY.md`.
- Found task commits: `44df4af`, `8c80a8b`, and `0869d61`.

---
*Phase: 02-core-rag-engine*
*Completed: 2026-05-01*
