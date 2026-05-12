---
phase: 05-mock-corpus-contract-and-safety-foundation
plan: 03
subsystem: cli-docs
tags: [python, typer, cli, markdown, privacy]
requires:
  - phase: 05-mock-corpus-contract-and-safety-foundation
    provides: Mock corpus generator and validator contracts from Plans 01-02
provides:
  - Flat `ood mock-init` and `ood mock-validate` commands
  - README workflow for privacy-safe mock data generation, validation, and Phase 6 handoff
affects: [phase-06-index-validation, user-workflows]
tech-stack:
  added: []
  patterns: [flat Typer commands, JSON/human dual output, quiet-mode support]
key-files:
  created: []
  modified: [src/ood/cli.py, tests/test_cli.py, README.md]
key-decisions:
  - "Keep mock corpus operations as flat Typer commands to preserve the existing CLI contract."
  - "Document that golden answers and expected sources belong in future evaluation JSON, never indexed Markdown."
patterns-established:
  - "Mock CLI commands emit `{command, ...result.to_dict()}` JSON for automation and concise human summaries for operators."
requirements-completed: [MOCK-01, MOCK-02, MOCK-03, MOCK-05]
duration: 1min
completed: 2026-05-03
---

# Phase 05 Plan 03: CLI and Docs Wiring for Generation and Validation Summary

**Flat CLI workflow for generating and validating synthetic mock corpora with README privacy-boundary guidance**

## Performance

- **Duration:** 1min
- **Started:** 2026-05-03T18:28:02Z
- **Completed:** 2026-05-03T18:32:37Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Added `ood mock-init` with target directory, dataset, JSON, and quiet options.
- Added `ood mock-validate` with corpus directory, JSON, verbose, and quiet options.
- Extended CLI tests to verify help output, JSON contracts, human summaries, and quiet mode.
- Documented the mock-data-only workflow, path overrides, validation boundary, and Phase 6 indexing handoff.

## Task Commits

1. **Task 1: Add flat mock corpus CLI commands** - `cc87b4d` (test), `a862409` (feat)
2. **Task 2: Document mock corpus workflow and safety boundaries** - `679636c` (docs)

## Files Created/Modified
- `src/ood/cli.py` - Mock corpus generation and validation CLI commands plus emitters.
- `tests/test_cli.py` - Mock CLI contract tests.
- `README.md` - Mock Corpus section with commands and safety guidance.

## Decisions Made
- Kept CLI output shape aligned with existing command JSON patterns by including `command` at the top level.
- Kept README examples local-first and synthetic-only, with explicit guidance against golden-answer leakage.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None.

## Verification

- `uv run pytest tests/test_cli.py tests/test_mock_corpus.py tests/test_mock_validation.py -q` — passed (27 tests).
- `uv run pytest -q` — passed (73 tests).

## Self-Check: PASSED

- Modified files exist: `src/ood/cli.py`, `tests/test_cli.py`, `README.md`.
- Commits verified in git log: `cc87b4d`, `a862409`, `679636c`.

## Next Phase Readiness

Phase 6 can use `ood mock-init`, `ood mock-validate`, and `ood index --knowledge-dir knowledge/mock/v1` to validate indexing over the generated mock corpus.

---
*Phase: 05-mock-corpus-contract-and-safety-foundation*
*Completed: 2026-05-03*
