---
phase: 06-mock-data-import-and-index-validation
plan: 01
subsystem: testing
tags: [mock-corpus, rag, indexing, manifest, fallback-index]
requires:
  - phase: 05-mock-corpus-contract-and-safety-foundation
    provides: Phase 5 generated mock Markdown corpus contract
provides:
  - Service-level proof that generated mock Markdown indexes through RagEngine as normal knowledge
  - Reindex boundary coverage for mock corpus storage rebuilds
affects: [phase-07-evaluation-dataset-and-metric-core, rag-indexing, mock-data]
tech-stack:
  added: []
  patterns: [pytest integration coverage, local fallback index verification]
key-files:
  created: [tests/test_mock_indexing.py]
  modified: []
key-decisions:
  - "Use RagEngine public index/reindex methods and local fallback mode to prove MOCK-04 without adding mock-specific production indexing logic."
patterns-established:
  - "Mock indexing tests generate the real Phase 5 corpus in tmp_path and inspect normal manifest plus fallback artifacts."
requirements-completed: [MOCK-04]
duration: 3min
completed: 2026-05-03
---

# Phase 06 Plan 01: Mock Corpus Indexing Summary

**Generated mock Markdown corpus validated through RagEngine index and reindex flows using normal manifest and fallback-index contracts**

## Performance

- **Duration:** 3min
- **Started:** 2026-05-03T18:52:00Z
- **Completed:** 2026-05-03T18:55:53Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- Added integration coverage proving `generate_mock_corpus()` output is accepted by `RagEngine.index_markdown()` without metadata warnings.
- Verified generated mock entries retain normal knowledge metadata in `ood-manifest.json` while fallback index content strips frontmatter.
- Added reindex coverage proving stale storage children are deleted while mock source files and sibling runtime data remain untouched.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add mock corpus index acceptance integration test** - `093676f` (test)
2. **Task 2: Add mock corpus reindex clean rebuild test** - `24f1088` (test)

## Files Created/Modified

- `tests/test_mock_indexing.py` - Service-level integration tests for mock corpus index and reindex behavior through `RagEngine`.

## Decisions Made

- Use RagEngine public index/reindex methods and local fallback mode to prove MOCK-04 without adding mock-specific production indexing logic.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

- `tests/test_mock_indexing.py:29` asserts `result.metadata_warnings == []`; this is an intentional verification of the plan requirement that generated mock metadata produces no warnings, not a stub flowing to runtime behavior.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Verification

- `uv run pytest tests/test_mock_indexing.py::test_generated_mock_corpus_indexes_as_normal_knowledge -q` — passed
- `uv run pytest tests/test_mock_indexing.py::test_mock_reindex_cleans_storage_without_touching_mock_corpus_or_data_siblings -q` — passed
- `uv run pytest tests/test_mock_indexing.py tests/test_rag.py -q` — 27 passed

## Next Phase Readiness

Phase 7 can rely on mock Markdown being importable via the same service-level index and reindex paths used by ordinary knowledge files.

---
*Phase: 06-mock-data-import-and-index-validation*
*Completed: 2026-05-03*

## Self-Check: PASSED
