---
phase: 02-core-rag-engine
plan: 03
subsystem: rag-service
tags: [python, lightrag, semantic-search, source-attribution, confidence, testing]

requires:
  - phase: 02-core-rag-engine
    provides: Markdown indexing, LightRAG storage setup, and credential-aware RagEngine construction
provides:
  - Retrieval-only semantic query behavior with stable QueryResult output when no LLM credentials are configured
  - Source attribution normalization with relative paths, bounded scores, excerpts, and deduplication
  - Instructional missing-index error before querying empty storage
  - Heuristic confidence scoring from retrieval signal and optional LLM availability
  - Credential-backed mix-mode query path with generated answers when configured
affects: [02-core-rag-engine, cli-query, rag-query, source-attribution]

tech-stack:
  added: []
  patterns: [sync wrapper around async LightRAG query, OOD-owned source normalization, deterministic heuristic confidence]

key-files:
  created: []
  modified: [src/ood/rag.py, tests/test_rag.py]

key-decisions:
  - "Keep query output behind QueryResult so LightRAG result shapes do not leak into CLI contracts."
  - "Use naive LightRAG retrieval without credentials and mix mode only when LLM credentials are configured."
  - "Compute confidence deterministically from retrieval signals instead of relying on LLM self-rating."

patterns-established:
  - "RagEngine.query() is a synchronous wrapper over _aquery() for CLI-friendly use while retaining async LightRAG calls internally."
  - "LightRAG chunks are normalized through OOD-owned helpers before reaching public SourceHit objects."

requirements-completed: [RAG-02, RAG-03, RAG-04, RAG-05, INF-03]

duration: 2min 39s
completed: 2026-05-01
---

# Phase 02 Plan 03: Semantic Query and Confidence Scoring Summary

**Semantic LightRAG querying with retrieval-only privacy fallback, ranked source attribution, and deterministic confidence scoring**

## Performance

- **Duration:** 2min 39s
- **Started:** 2026-05-01T13:02:17Z
- **Completed:** 2026-05-01T13:04:56Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `RagEngine.query()` with missing-index validation and a stable `QueryResult` contract for semantic queries.
- Normalized LightRAG query chunks into deduplicated `SourceHit` objects with relative source paths, clamped scores, and 500-character excerpts.
- Preserved privacy fallback behavior: missing LLM credentials use `QueryParam(mode="naive")`, return `answer=None`, and never invoke the Cloud LLM adapter.
- Added heuristic confidence scoring from top score, source count, score spread, and LLM availability.
- Added credential-backed query behavior that selects `QueryParam(mode="mix")`, passes a non-noop LLM function, and returns generated answers when available.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: Retrieval-only query and source normalization tests** - `60a6e1f` (test)
2. **Task 1 GREEN: Retrieval-only query and source normalization** - `1719520` (feat)
3. **Task 2 RED: Confidence and LLM query path tests** - `c255e03` (test)
4. **Task 2 GREEN: Confidence scoring and LLM query path** - `0b8dd75` (feat)

## Files Created/Modified

- `src/ood/rag.py` - Adds query execution, missing-index checks, LightRAG query mode selection, chunk-to-source normalization, optional generated answers, and confidence scoring.
- `tests/test_rag.py` - Adds contract tests for retrieval-only queries, no-credential privacy behavior, missing-index errors, confidence scoring, mix-mode selection, and non-noop LLM adapter wiring.

## Decisions Made

- Kept the public query contract in OOD dataclasses so CLI and automation remain insulated from LightRAG response-shape changes.
- Selected `naive` query mode whenever credentials are absent to satisfy retrieval-only privacy behavior, and selected `mix` mode only for configured LLM-backed queries.
- Used deterministic confidence scoring from retrieval evidence and LLM availability so tests and automation do not depend on model self-assessment.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected confidence test expectation to match the specified formula**
- **Found during:** Task 2 (Add heuristic confidence and optional LLM-backed answer path)
- **Issue:** The initial failing test expected `0.86`, but the plan's exact formula for the fixture scores `0.9`, `0.6`, and `0.2` produces `0.92`.
- **Fix:** Updated the test expectation to `0.92` while implementing the planned formula exactly.
- **Files modified:** `tests/test_rag.py`
- **Verification:** `uv run pytest tests/test_rag.py::test_confidence_score_uses_retrieval_signal_and_llm_availability tests/test_rag.py::test_llm_credentials_select_mix_query_mode tests/test_rag.py::test_llm_credentials_pass_non_noop_lightrag_llm_func_for_query -q`
- **Committed in:** `0b8dd75`

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** The fix aligned the test with the plan's required formula; no scope was added.

## Issues Encountered

- Pre-existing untracked planning files remain in `.planning/phases/02-core-rag-engine/`; they were not created by this plan and were left untouched except for the new `02-03-SUMMARY.md`.
- No authentication gates or external-service setup were required.
- No secrets were configured, logged, or committed.

## Known Stubs

None - no placeholder or UI-facing empty-data stubs were introduced in the files modified by this plan.

## User Setup Required

None - no external service configuration required for retrieval-only query behavior. LLM-backed answers activate only when credentials are configured through the existing settings mechanism.

## Next Phase Readiness

- Plan 02-04 can wire `ood query` to `RagEngine.query()` and render the stable `QueryResult.to_dict()` payload for JSON output.
- The query service now satisfies source attribution, score, confidence, and missing-index contracts needed by the CLI integration plan.

## Self-Check: PASSED

- Found modified implementation file: `src/ood/rag.py`.
- Found modified test file: `tests/test_rag.py`.
- Found summary file: `.planning/phases/02-core-rag-engine/02-03-SUMMARY.md`.
- Found task commits: `60a6e1f`, `1719520`, `c255e03`, and `0b8dd75`.

---
*Phase: 02-core-rag-engine*
*Completed: 2026-05-01*
