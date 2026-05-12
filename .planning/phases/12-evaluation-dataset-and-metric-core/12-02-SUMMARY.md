---
phase: 12-evaluation-dataset-and-metric-core
plan: 02
subsystem: evaluation
tags: [evaluation, retrieval-metrics, hit-rate, mrr, pytest]
requires:
  - phase: 12-evaluation-dataset-and-metric-core
    provides: EvaluationCase expected and forbidden source contracts
provides:
  - pure retrieval metric functions for Hit@1, Hit@3, Hit@5, MRR, source recall, and forbidden-source rate
  - stable per-case and aggregate metric dataclasses with report-ready to_dict output
affects: [phase-13-evaluation-cli, retrieval-quality, regression-baseline]
tech-stack:
  added: []
  patterns: [pure-metric-functions, exact-posix-path-comparison, rounded-aggregate-reporting]
key-files:
  created:
    - src/ood/evaluation_metrics.py
    - tests/test_evaluation_metrics.py
  modified: []
key-decisions:
  - "Compute retrieval metrics only from EvaluationCase and ordered SourceHit.path values, keeping retrieval backends black-box for Phase 13."
  - "Deduplicate returned paths for recall and forbidden checks while preserving first rank for Hit@k and MRR."
patterns-established:
  - "Metric functions are deterministic, side-effect-free, and do not call RagEngine or external services."
  - "Aggregate metric floats are rounded to four decimals for stable JSON/report comparisons."
requirements-completed: [EVAL-03]
duration: 8min
completed: 2026-05-08
---

# Phase 12 Plan 02: Retrieval Metric Core Summary

**Pure retrieval-quality formulas for ranked SourceHit lists with stable per-case and aggregate report output**

## Performance

- **Duration:** 8min
- **Started:** 2026-05-08T09:32:22Z
- **Completed:** 2026-05-08T09:40:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `evaluate_retrieval_case()` for Hit@1/3/5, MRR, source recall, forbidden hit flags, offending paths, and first relevant rank.
- Added `summarize_retrieval_metrics()` for aggregate retrieval rates with zero-case safety and four-decimal rounding.
- Covered empty results, partial recall, duplicate returned sources, and forbidden-source hits with focused tests.

## Task Commits

1. **Task 1: Implement per-case retrieval metrics** - `abd58b0` (test), `6479de8` (feat)
2. **Task 2: Aggregate retrieval metrics across cases** - `0a4309b` (test), `7dd6d47` (feat)

_Note: TDD tasks have test → feat commits._

## Files Created/Modified

- `src/ood/evaluation_metrics.py` - Retrieval metric dataclasses, per-case formula, aggregate summary formula, and public exports.
- `tests/test_evaluation_metrics.py` - Formula and edge-case tests using only public `EvaluationCase` and `SourceHit` contracts.

## Decisions Made

- Compute retrieval metrics only from `EvaluationCase` and ordered `SourceHit.path` values, keeping retrieval backends black-box for Phase 13.
- Deduplicate returned paths for recall and forbidden checks while preserving first rank for Hit@k and MRR.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Verification

- `uv run pytest tests/test_evaluation_metrics.py -q` → 5 passed

## Next Phase Readiness

Plan 12-03 can add ticket-intelligence metrics alongside retrieval metrics before Phase 13 wires both through black-box evaluation runs.

## Self-Check: PASSED

- Found `src/ood/evaluation_metrics.py` and `tests/test_evaluation_metrics.py`.
- Verified task commits exist in recent git history: `abd58b0`, `6479de8`, `0a4309b`, `7dd6d47`.

---
*Phase: 12-evaluation-dataset-and-metric-core*
*Completed: 2026-05-08*
