---
phase: 14-baseline-feedback-loop-and-review-gate
plan: 03
subsystem: cli-evaluation
tags: [python, typer, pytest, evaluation, baseline, review-gate]

requires:
  - phase: 14-baseline-feedback-loop-and-review-gate
    provides: observational baseline helpers and review artifact creation commands from Plans 01/02
provides:
  - `ood eval decide` for approved/rejected/deferred review decisions
  - `ood eval update-baseline` gated by explicit approved review decisions
  - README local mock-data → evaluation → review → baseline-update workflow
affects: [phase-14, evaluation-cli, baseline-workflow, review-gate]

tech-stack:
  added: []
  patterns:
    - Typer subcommands remain under the existing `ood eval` namespace
    - Review gate uses `can_update_baseline` before writing `current.json`

key-files:
  created:
    - .planning/phases/14-baseline-feedback-loop-and-review-gate/14-03-SUMMARY.md
  modified:
    - src/ood/eval_cli.py
    - tests/test_eval_cli.py
    - README.md

key-decisions:
  - "Keep baseline updates as explicit, review-gated CLI actions; metric improvement alone never updates `current.json`."
  - "Preserve per-case `proposed_fix_type` and `proposed_fix_notes` while applying top-level review decisions and baseline update state."

patterns-established:
  - "Decision CLI pattern: load review JSON, apply service-layer decision helper, write JSON back to the chosen target path."
  - "Baseline update gate pattern: load review, require `can_update_baseline`, then save an observational baseline and mark only the top-level review status as updated."

requirements-completed: [EVAL-05, EVAL-11]

duration: 2m 10s
completed: 2026-05-11
---

# Phase 14 Plan 03: Review Gate CLI and Baseline Loop Summary

**Explicit review decisions and gated baseline updates for local evaluation reports, with README workflow commands for the full mock-data feedback loop.**

## Performance

- **Duration:** 2m 10s
- **Started:** 2026-05-11T11:09:04Z
- **Completed:** 2026-05-11T11:11:14Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added `ood eval decide` to record approved, rejected, and deferred review decisions, reviewer identity, rationale, and requested baseline update state without losing proposed fix metadata.
- Added `ood eval update-baseline` to enforce `can_update_baseline(review)` before writing `data/evaluation/baselines/current.json`, and to mark the review top-level `baseline_update_status` as `updated` only after success.
- Documented the complete local loop in README: regenerate mock data, reindex, smoke query, evaluate, create baseline, review, decide, and update the baseline only when approved.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add `ood eval decide` and gated `update-baseline` commands**
   - `23c0215` test(14-03): add failing review gate CLI tests
   - `2e9e887` feat(14-03): implement review gate CLI commands
2. **Task 2: Document the local baseline/review workflow**
   - `4d44385` docs(14-03): document baseline review workflow

**Plan metadata:** `2dad09e` docs(14-03): complete review gate plan

## Files Created/Modified

- `src/ood/eval_cli.py` - Imports Plan 01 review helpers and exposes `decide` plus `update-baseline` commands under `ood eval`.
- `tests/test_eval_cli.py` - Covers decision outcomes, invalid decisions, metadata preservation, approved update success, and rejected/deferred/missing-approval blocking.
- `README.md` - Replaces future-only evaluation CLI wording with the current baseline/review gate workflow and proposed fix metadata guidance.

## Decisions Made

- Keep baseline updates as explicit, review-gated CLI actions; metric improvement alone never updates `current.json`.
- Preserve per-case `proposed_fix_type` and `proposed_fix_notes` while applying top-level review decisions and baseline update state.

## Deviations from Plan

None - plan executed exactly as written.

## Auth Gates

None.

## Known Stubs

None. Stub scan found only intentional internal/test empty accumulators and assertions, not user-facing placeholder data or unwired UI output.

## Issues Encountered

None.

## Verification

- `uv run pytest tests/test_eval_cli.py tests/test_eval_baseline.py -q` → 60 passed
- `uv run python -c "from ood.eval_cli import eval_app; print('ok')"` → ok
- `uv run ood eval --help` → lists `run`, `cases`, `baseline`, `review`, `decide`, and `update-baseline`

## Self-Check: PASSED

- Found modified files: `src/ood/eval_cli.py`, `tests/test_eval_cli.py`, `README.md`
- Found summary file: `.planning/phases/14-baseline-feedback-loop-and-review-gate/14-03-SUMMARY.md`
- Found task commits: `23c0215`, `2e9e887`, `4d44385`

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Phase 14 now provides an end-to-end local baseline and review gate loop for v1.1 evaluation improvement work. Future threshold or trend automation can build on explicit review artifacts instead of inferring acceptance from metrics alone.

---
*Phase: 14-baseline-feedback-loop-and-review-gate*
*Completed: 2026-05-11*
