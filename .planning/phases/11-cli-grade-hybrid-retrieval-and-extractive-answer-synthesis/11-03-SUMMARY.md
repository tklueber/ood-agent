---
phase: 11-cli-grade-hybrid-retrieval-and-extractive-answer-synthesis
plan: 03
subsystem: cli-docs
tags: [cli, diagnostics, graph-retrieval, docs]
requires: [GRAPH-01, CLI-01]
provides: [graph_defer_status, verbose_query_diagnostics, readme_query_workflow]
affects: [src/ood/rag.py, src/ood/cli.py, tests/test_cli.py, README.md]
tech_stack:
  added: []
  patterns: [public-query-contract, documented-defer-decision]
key_files:
  created: []
  modified: [src/ood/cli.py, tests/test_cli.py, README.md]
decisions:
  - "Defer graph retrieval until a deterministic local graph artifact and privacy-safe tests exist."
  - "Keep JSON output as QueryResult.to_dict() and render only non-secret diagnostics in verbose human output."
metrics:
  duration: "part of phase execution"
  completed: 2026-05-04
---

# Phase 11 Plan 03: Graph-Retrieval Defer Status plus CLI/Docs Diagnostics Summary

Query output now makes graph retrieval status explicit and documents the Phase 11 local workflow for hybrid retrieval, extractive answers, and skill-usable diagnostics.

## Completed Tasks

1. Added graph-retrieval defer metadata to query diagnostics and rendered retrieval backend, strategy, extractive mode, and graph status in `ood query --verbose`.
2. Updated README with hybrid retrieval, local extractive answer synthesis, JSON diagnostics, and GRAPH-01 defer rationale/risk/activation criteria.

## Verification

- `uv run pytest tests/test_models.py tests/test_rag.py tests/test_cli.py -q` — 59 passed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Critical Functionality] Preserved JSON contract by keeping diagnostics in QueryResult**
- **Found during:** Task 1
- **Issue:** CLI diagnostics must not add CLI-only JSON fields.
- **Fix:** Verbose human output reads `result.retrieval_diagnostics`; JSON remains exactly `QueryResult.to_dict()`.
- **Files modified:** `src/ood/cli.py`, `tests/test_cli.py`
- **Commit:** `8b6142c`

## Known Stubs

None.

## Self-Check: PASSED

- CLI/docs changes committed in `8b6142c`.
- Targeted verification passed with 59 tests.
