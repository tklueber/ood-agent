---
phase: 14-baseline-feedback-loop-and-review-gate
plan: 02
subsystem: evaluation-cli
tags: [evaluation, cli, typer, baseline, review-artifacts, tdd]
requires:
  - phase: 14-baseline-feedback-loop-and-review-gate
    provides: Observational baseline and review artifact helpers in `ood.eval_baseline`
  - phase: 13-evaluation-service-and-cli-reporting
    provides: `ood eval` Typer namespace and schema_version=1 eval report JSON
provides:
  - `ood eval baseline` command for deliberate observational baseline creation from an existing eval report
  - `ood eval review` command for failed/errored review artifact generation with proposed fix metadata
  - CLI tests for default ignored artifact paths, German messages, compact JSON output, and import safety
affects: [phase-14-plan-03, evaluation-feedback-loop, baseline-review-gate]
tech-stack:
  added: []
  patterns:
    - "Phase 14 artifact helpers are exposed through the existing reverse-import-safe `eval_app` namespace without changing `ood eval run`."
    - "Generated baseline/review artifacts default to ignored `data/evaluation/...` paths unless users pass explicit `--out` paths."
key-files:
  created: []
  modified:
    - src/ood/eval_cli.py
    - tests/test_eval_cli.py
key-decisions:
  - "Keep baseline creation as an explicit `ood eval baseline --report ...` user action rather than auto-promoting `ood eval run --out` reports."
  - "Keep review JSON actionable and machine-readable by surfacing the allowed `PROPOSED_FIX_TYPES` vocabulary in `ood eval review --json`."
patterns-established:
  - "Baseline/review CLI commands catch report loading and schema errors at the Typer boundary, emit German error messages, and exit 1."
  - "Human CLI strings remain German while JSON keys remain English and compact on stdout."
requirements-completed: [EVAL-05, EVAL-11]
duration: 3m 11s
completed: 2026-05-11
---

# Phase 14 Plan 02: Eval Baseline and Review CLI Summary

**`ood eval baseline` and `ood eval review` now turn schema_version=1 evaluation reports into explicit observational baselines and failed-case review artifacts under ignored runtime defaults, preserving proposed fix metadata for the next review gate.**

## Performance

- **Duration:** 3m 11s
- **Started:** 2026-05-11T11:04:11Z
- **Completed:** 2026-05-11T11:07:22Z
- **Tasks:** 2 (both TDD)
- **Files modified:** 2
- **Tests added:** 10 focused CLI tests

## Accomplishments

- Added `ood eval baseline --report <report.json> [--out <baseline.json>]` to save observational baseline artifacts with `thresholds: null`, `gate_mode: review_required`, German success/errors, and compact JSON summaries.
- Added `ood eval review --report <report.json> [--out <review.json>]` to persist failed/errored case review artifacts only, with deferred decisions and default `proposed_fix_type: investigate` metadata from the Phase 14 helper layer.
- Preserved the Phase 13 import-safety invariant by adding all imports and commands after `eval_app = typer.Typer(...)` and keeping `from ood.cli import (...)` in its established location.

## Task Commits

Each task was committed atomically:

1. **Task 1 RED: baseline CLI tests** — `9c680b9` (test)
2. **Task 1 GREEN: baseline CLI command** — `41ef1da` (feat)
3. **Task 2 RED: review CLI tests** — `83ebd20` (test)
4. **Task 2 GREEN: review CLI command** — `8c36703` (feat)

_Note: Both plan tasks were marked TDD, so each task has a failing-test commit and an implementation commit._

## Files Created/Modified

- `src/ood/eval_cli.py` — imports Phase 14 artifact helpers, defines shared report/output option types, adds `_default_review_path`, and exposes `baseline`/`review` commands under `eval_app`.
- `tests/test_eval_cli.py` — adds baseline and review CLI coverage for help flags, artifact writing, default ignored paths, JSON stdout, German error messages, and allowed proposed fix types.

## Decisions Made

- Baseline and review output paths are reported exactly as resolved by CLI options/defaults rather than force-resolved absolute paths, matching existing CLI path style and tests.
- Default review filenames use `meta.dataset` plus the first 8 characters of `meta.dataset_hash`, with `/` and spaces sanitized to `-`, so generated artifacts are stable and readable.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Auth Gates

None. All work is local CLI/report artifact generation and requires no external credentials.

## Known Stubs

None. The stub scan only found existing option defaults (`= None`) and local empty accumulator variables in `src/ood/eval_cli.py`; these do not flow to UI rendering and are not placeholder data sources.

## Deferred Issues

None within scope. Pre-existing untracked/modified files visible in `git status` were left untouched because they are outside this plan.

## Verification

- `uv run pytest tests/test_eval_cli.py -q` → **34 passed**
- `uv run pytest tests/test_eval_cli.py tests/test_eval_baseline.py -q` → **51 passed**
- `uv run python -c "from ood.eval_cli import eval_app; print('ok')"` → `ok`
- `uv run ood eval baseline --help` → exits 0
- `uv run ood eval review --help` → exits 0
- Acceptance marker checks for `@eval_app.command("baseline")`, `@eval_app.command("review")`, default `data/evaluation/...` paths, German messages, and `PROPOSED_FIX_TYPES` all passed.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 14 Plan 03 can now consume review artifacts from `ood eval review` and enforce explicit reviewer decisions before baseline updates.
- `ood eval baseline` provides the deliberate observational baseline snapshot required by EVAL-05 without adding thresholds or CI gate behavior.

## Self-Check: PASSED

Files exist:

- `src/ood/eval_cli.py` → FOUND
- `tests/test_eval_cli.py` → FOUND
- `.planning/phases/14-baseline-feedback-loop-and-review-gate/14-02-SUMMARY.md` → FOUND

Commits exist in `git log --oneline -8`:

- `9c680b9` → FOUND
- `41ef1da` → FOUND
- `83ebd20` → FOUND
- `8c36703` → FOUND

---
*Phase: 14-baseline-feedback-loop-and-review-gate*
*Completed: 2026-05-11*
