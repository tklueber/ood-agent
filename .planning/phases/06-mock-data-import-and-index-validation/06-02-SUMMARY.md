---
phase: 06-mock-data-import-and-index-validation
plan: 02
subsystem: cli-docs
tags: [mock-corpus, cli, index, reindex, update, documentation]
requires:
  - phase: 05-mock-corpus-contract-and-safety-foundation
    provides: mock-init and mock-validate CLI commands plus generated corpus contract
provides:
  - CLI proof that mock corpus imports through existing index and reindex commands
  - CLI proof that mock corpus update reports add/change/unchanged/delete manifest diagnostics
  - README workflow for MOCK-04 local import and index validation
affects: [phase-07-evaluation-dataset-and-metric-core, user-workflows, mock-data]
tech-stack:
  added: []
  patterns: [Typer CLI smoke coverage, manifest lifecycle diagnostics]
key-files:
  created: []
  modified: [tests/test_cli.py, README.md]
key-decisions:
  - "Validate mock import through existing index, reindex, and update CLI commands with path overrides instead of adding mock-only index commands."
patterns-established:
  - "CLI mock workflow tests generate the corpus via mock-init and then exercise ordinary knowledge commands in local fallback mode."
requirements-completed: [MOCK-04]
duration: 3min
completed: 2026-05-03
---

# Phase 06 Plan 02: Mock CLI and Documentation Summary

**Mock corpus import validated through existing CLI index, reindex, and update commands with documented local workflow**

## Performance

- **Duration:** 3min
- **Started:** 2026-05-03T18:56:00Z
- **Completed:** 2026-05-03T18:59:30Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- Added CLI smoke coverage for `mock-init` followed by existing `index` and `reindex` commands using `--knowledge-dir` and `--storage-dir` overrides.
- Added CLI lifecycle coverage for `update --json`, proving added, changed, unchanged, and deleted mock paths are surfaced through manifest diagnostics.
- Expanded README with a copy-paste MOCK-04 workflow and clarified that import/index validation remains local and uses no mock-only index command.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add CLI smoke tests for mock index and reindex path overrides** - `dde6a63` (test)
2. **Task 2: Add CLI update diagnostics test for mock add/change/delete lifecycle** - `78e7aba` (test)
3. **Task 3: Document mock import and index validation workflow** - `6379d24` (docs)

## Files Created/Modified

- `tests/test_cli.py` - CLI-level tests for mock corpus index, reindex, and update workflows through existing commands.
- `README.md` - Mock import and index validation instructions using normal path overrides.

## Decisions Made

- Validate mock import through existing index, reindex, and update CLI commands with path overrides instead of adding mock-only index commands.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

- `tests/test_cli.py:523` asserts `payload["metadata_warnings"] == []`; this is an intentional diagnostic assertion that generated mock files produce no CLI metadata warnings, not a runtime stub.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Verification

- `uv run pytest tests/test_cli.py::test_mock_corpus_indexes_and_reindexes_through_existing_cli_commands -q` — passed
- `uv run pytest tests/test_cli.py::test_mock_corpus_update_reports_added_changed_unchanged_and_deleted_paths -q` — passed
- `uv run pytest tests/test_cli.py::test_mock_corpus_indexes_and_reindexes_through_existing_cli_commands tests/test_cli.py::test_mock_corpus_update_reports_added_changed_unchanged_and_deleted_paths -q` — 2 passed
- `uv run pytest tests/test_cli.py -q` — 18 passed
- `uv run pytest -q` — 77 passed

## Next Phase Readiness

Phase 7 can use the documented CLI workflow and manifest diagnostics as a reproducible way to build and inspect the mock knowledge base before evaluations.

---
*Phase: 06-mock-data-import-and-index-validation*
*Completed: 2026-05-03*

## Self-Check: PASSED
