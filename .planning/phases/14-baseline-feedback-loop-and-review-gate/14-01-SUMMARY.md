---
phase: 14-baseline-feedback-loop-and-review-gate
plan: 01
subsystem: evaluation
tags: [python, pytest, json, baseline, review-gate]

requires:
  - phase: 13-evaluation-service-and-cli-reporting
    provides: schema_version=1 eval report payloads consumed by baseline and review artifacts
provides:
  - Pure observational baseline JSON helpers for schema_version=1 eval reports
  - Failed/errored case review artifact helpers with evidence and proposed fix fields
  - Explicit approved-review predicate for future baseline update commands
affects: [phase-14-cli, evaluation-workflow, baseline-review-gate]

tech-stack:
  added: []
  patterns:
    - stdlib-only JSON artifact layer with stable provenance hashes
    - observational baseline snapshots with thresholds explicitly null
    - review-gated baseline updates requiring approved human decision and reviewer identity

key-files:
  created:
    - src/ood/eval_baseline.py
    - tests/test_eval_baseline.py
  modified: []

key-decisions:
  - "Keep Phase 14 Plan 01 as a pure stdlib artifact layer: no CLI wiring, no new dependencies, no metric recomputation."
  - "Represent first baselines as observational snapshots with thresholds: null and gate_mode: review_required rather than hard pass/fail thresholds."
  - "Require an approved review, reviewer identity, and requested/approved baseline_update_status before can_update_baseline returns true."

patterns-established:
  - "Baseline artifacts wrap the existing schema_version=1 report without re-keying report meta, summary, or cases."
  - "Review artifacts include only failed/errored cases and preserve expected/actual evidence plus retrieval and ticket metrics."
  - "Proposed fix types are exported constants so downstream CLI code shares the same machine-readable vocabulary."

requirements-completed: [EVAL-05, EVAL-11]

duration: 2m 52s
completed: 2026-05-11
---

# Phase 14 Plan 01: Baseline Artifact Layer Summary

**Observational eval baselines and evidence-rich failed-case review artifacts with an explicit approved-review gate.**

## Performance

- **Duration:** 2m 52s
- **Started:** 2026-05-11T10:57:09Z
- **Completed:** 2026-05-11T11:00:01Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Added `src/ood/eval_baseline.py` with pure JSON load/write helpers, stable report hashing, schema_version=1 eval report validation, and observational baseline construction/persistence.
- Added review artifact construction/persistence that filters failed and errored cases, preserves report evidence, and defaults decisions/proposed fixes to deferred investigation.
- Added review-decision application and `can_update_baseline` so future CLI commands can require explicit approved review status before replacing baselines.
- Added 17 focused pytest cases covering baseline schema, no-threshold invariants, review evidence extraction, proposed fix vocabulary, decision application, persistence, and the approval gate.

## Task Commits

Each task was committed atomically using TDD commits:

1. **Task 1: Add observational baseline snapshot helpers**
   - `29b7622` test: add failing observational baseline tests
   - `cde2228` feat: implement observational baseline helpers
2. **Task 2: Add review artifact helpers, proposed fix fields, and approval gate predicate**
   - `da6fa85` test: add failing review artifact gate tests
   - `dc98636` feat: implement review artifacts and baseline gate

## Files Created/Modified

- `src/ood/eval_baseline.py` - Pure artifact helper module exporting baseline, review, decision, JSON IO, vocabulary constants, and approval-gate predicate.
- `tests/test_eval_baseline.py` - Focused TDD coverage for baseline snapshots, review artifacts, proposed fix vocabulary, persistence, and approval gate behavior.

## Decisions Made

- Kept the artifact layer stdlib-only and independent of CLI wiring, matching Plan 01's boundary and preserving later Plan 02/03 integration points.
- Preserved the full existing eval report inside baseline artifacts instead of mapping metrics into a new schema, avoiding Phase 13 report drift.
- Required a non-empty reviewer on `can_update_baseline` in addition to approved decision and requested/approved update status because the plan explicitly says missing reviewer must not approve replacement.

## Deviations from Plan

None - plan executed as written.

## Known Stubs

None - no placeholder, TODO/FIXME, or mock-only implementation remains in created files.

## Issues Encountered

- The Task 2 RED tests initially needed to align with the stated missing-reviewer gate; the GREEN implementation and tests now assert that an approved decision without reviewer remains blocked.

## Verification

- `uv run pytest tests/test_eval_baseline.py -q` → 17 passed
- `uv run python -c "from ood.eval_baseline import build_observational_baseline, build_review_artifact, can_update_baseline; print('ok')"` → `ok`

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02 can import `save_observational_baseline` and `save_review_artifact` for `ood eval baseline` / `ood eval review` commands.
- Plan 03 can use `apply_review_decision` and `can_update_baseline` to enforce the explicit review gate before replacing `data/evaluation/baselines/current.json`.

## Self-Check: PASSED

- FOUND: `src/ood/eval_baseline.py`
- FOUND: `tests/test_eval_baseline.py`
- FOUND: `.planning/phases/14-baseline-feedback-loop-and-review-gate/14-01-SUMMARY.md`
- FOUND commits: `29b7622`, `cde2228`, `da6fa85`, `dc98636`

---
*Phase: 14-baseline-feedback-loop-and-review-gate*
*Completed: 2026-05-11*
