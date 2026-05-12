---
phase: 05-mock-corpus-contract-and-safety-foundation
plan: 01
subsystem: mock-data
tags: [python, markdown, mock-corpus, privacy, tdd]
requires:
  - phase: 03-knowledge-management
    provides: Markdown frontmatter import contract and metadata expectations
provides:
  - Deterministic synthetic Markdown corpus generator
  - MockDocument and MockCorpusResult contracts
  - Source-type-complete mock corpus fixture foundation
affects: [phase-06-index-validation, phase-07-evaluation-dataset]
tech-stack:
  added: []
  patterns: [frozen dataclasses, dependency-free scalar frontmatter rendering, deterministic file generation]
key-files:
  created: [src/ood/mock_corpus.py, tests/test_mock_corpus.py]
  modified: []
key-decisions:
  - "Use dependency-free deterministic YAML-like scalar rendering so mock files follow the existing Phase 3 Markdown parser contract."
  - "Keep generated Markdown free of expected answers and hidden labels so Phase 7 evaluation data remains separate from indexed knowledge."
patterns-established:
  - "Mock files must include mock: true, dataset, synthetic_id, source_type, scenario/routing/risk metadata, and a visible body warning."
requirements-completed: [MOCK-01, MOCK-02]
duration: 2min
completed: 2026-05-03
---

# Phase 05 Plan 01: Mock Corpus Contracts and Deterministic Markdown Generator Summary

**Dependency-free synthetic Markdown corpus generator with mandatory mock metadata, visible warnings, and six-source-type coverage**

## Performance

- **Duration:** 2min
- **Started:** 2026-05-03T18:28:02Z
- **Completed:** 2026-05-03T18:32:37Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added `MockDocument` and `MockCorpusResult` contracts with JSON-safe serialization.
- Implemented `generate_mock_corpus()` to write 12 importable Markdown files under source-type folders.
- Covered tickets, wiki articles, Jira bugs, ServiceNow cases, runbooks, and notes with synthetic identifiers and warnings.

## Task Commits

1. **Task 1: Define mock corpus result contracts** - `e8cfdf8` (test), `75efdf1` (feat)
2. **Task 2: Implement deterministic broad mock corpus generation** - `9fa791a` (test), `b99d130` (feat)

## Files Created/Modified
- `src/ood/mock_corpus.py` - Mock corpus dataclasses and deterministic generator.
- `tests/test_mock_corpus.py` - Contract tests for metadata, warnings, coverage, and safe generated content.

## Decisions Made
- Used only stdlib dataclasses/pathlib to preserve the no-new-dependency plan.
- Stored operational coverage labels in frontmatter but omitted golden answers from document bodies.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Verification

- `uv run pytest tests/test_mock_corpus.py -q` — passed (5 tests).

## Self-Check: PASSED

- Created files exist: `src/ood/mock_corpus.py`, `tests/test_mock_corpus.py`.
- Commits verified in git log: `e8cfdf8`, `75efdf1`, `9fa791a`, `b99d130`.

## Next Phase Readiness

Plan 02 can validate the generated corpus for safety markers and coverage dimensions.

---
*Phase: 05-mock-corpus-contract-and-safety-foundation*
*Completed: 2026-05-03*
