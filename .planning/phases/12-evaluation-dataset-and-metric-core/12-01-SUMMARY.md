---
phase: 12-evaluation-dataset-and-metric-core
plan: 01
subsystem: evaluation
tags: [evaluation, dataset, json, mock-corpus, pytest]
requires:
  - phase: 05-mock-corpus-contract-and-safety-foundation
    provides: synthetic mock corpus generator and path contract
provides:
  - typed EvaluationDataset and EvaluationCase JSON loading contracts
  - deterministic evaluation fixture validation against mock knowledge paths
  - initial evaluation/datasets/mock-v1.json labels outside indexed Markdown
affects: [phase-13-evaluation-cli, retrieval-quality, ticket-intelligence]
tech-stack:
  added: []
  patterns: [stdlib-json-validation, frozen-dataclasses, portable-posix-source-paths]
key-files:
  created:
    - src/ood/evaluation.py
    - tests/test_evaluation.py
    - evaluation/datasets/mock-v1.json
  modified: []
key-decisions:
  - "Keep evaluation labels in versioned JSON outside indexed Markdown so mock knowledge remains retrieval input only."
  - "Validate expected and forbidden source paths as portable POSIX-relative paths before evaluation execution."
patterns-established:
  - "Evaluation dataset loading is pure stdlib JSON parsing with frozen dataclasses and actionable EvaluationDatasetError messages."
  - "Fixture tests generate the mock corpus into a temp directory and validate source references without indexing or Cloud LLM usage."
requirements-completed: [EVAL-01]
duration: 10min
completed: 2026-05-08
---

# Phase 12 Plan 01: Evaluation Dataset Contract and Mock Fixture Summary

**Versioned mock-v1 evaluation JSON with typed dataclass loading, source-reference validation, and labels kept outside indexed Markdown**

## Performance

- **Duration:** 10min
- **Started:** 2026-05-08T09:22:00Z
- **Completed:** 2026-05-08T09:32:21Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added `EvaluationDataset`, `EvaluationCase`, expected identifier/risk dataclasses, and `load_evaluation_dataset()` with deterministic validation errors.
- Enforced safe portable source references by rejecting absolute paths and `..` traversal and optionally verifying paths against a generated mock corpus.
- Added `evaluation/datasets/mock-v1.json` with Police, Offerten, DMS self-solve, and Rückfrage scenarios.

## Task Commits

1. **Task 1: Define evaluation dataset contracts and loader** - `d1cf20f` (test), `05ddf23` (feat)
2. **Task 2: Add the initial mock-v1 evaluation fixture** - `35deba6` (test), `d01c564` (feat)

_Note: TDD tasks have test → feat commits._

## Files Created/Modified

- `src/ood/evaluation.py` - Pure JSON loader, frozen dataset/case dataclasses, validation helpers, and public exports.
- `tests/test_evaluation.py` - Focused loader/fixture validation tests including malformed schema and missing source references.
- `evaluation/datasets/mock-v1.json` - Initial versioned synthetic evaluation fixture with expected/forbidden sources and ticket labels.

## Decisions Made

- Keep evaluation labels in versioned JSON outside indexed Markdown so mock knowledge remains retrieval input only.
- Validate expected and forbidden source paths as portable POSIX-relative paths before evaluation execution.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Verification

- `uv run pytest tests/test_evaluation.py -q` → 10 passed

## Next Phase Readiness

Plan 12-02 can consume `EvaluationCase.expected_sources` and `forbidden_sources` to compute retrieval metrics without invoking retrieval backends.

## Self-Check: PASSED

- Found `src/ood/evaluation.py`, `tests/test_evaluation.py`, and `evaluation/datasets/mock-v1.json`.
- Verified task commits exist in recent git history: `d1cf20f`, `05ddf23`, `35deba6`, `d01c564`.

---
*Phase: 12-evaluation-dataset-and-metric-core*
*Completed: 2026-05-08*
