---
phase: 15-local-graph-metadata-retrieval-and-data-quality-review
plan: 03
subsystem: cli-docs
tags: [cli, diagnostics, README]
requires: [15-02]
provides: [verbose-fusion-diagnostics, graph-retrieval-readme]
affects: [src/ood/cli.py, tests/test_cli.py, README.md]
tech_stack:
  added: []
  patterns: [stable-json-contract, verbose-human-diagnostics]
key_files:
  created: []
  modified: [src/ood/cli.py, tests/test_cli.py, README.md]
decisions:
  - Keep query JSON unchanged as `QueryResult.to_dict()` while rendering CLI-only readability improvements only in verbose human output.
metrics:
  duration: 10min
  completed: 2026-05-08
  tasks: 2
  files: 3
---

# Phase 15 Plan 03: CLI and README Graph Diagnostics Summary

Operators can now inspect graph/metadata retrieval status and top-source fusion components directly in verbose query output while README documents the local-only OOD-KB workflow.

## Completed Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 RED | Failing CLI fusion diagnostics test | 5802af8 | tests/test_cli.py |
| 1 GREEN | Render graph fusion CLI diagnostics | 2b2bff7 | src/ood/cli.py |
| 2 | Document local graph retrieval diagnostics | 8e2c3c4 | README.md |

## What Changed

- Verbose `ood query` output now shows graph document/edge counts and top 3 score components as semantic, lexical, metadata, graph, and final values.
- JSON output remains exactly the public `QueryResult.to_dict()` contract.
- README now documents `ood-local-graph-index.json`, local-only graph/metadata signals, TraceId/Kafka commands against the external OOD-KB path, and the no-Cloud-LLM privacy boundary.

## Verification

- `uv run pytest tests/test_cli.py tests/test_rag.py tests/test_models.py -q` → 66 passed.

## Deviations from Plan

None - plan executed as written.

## Known Stubs

None.

## Self-Check: PASSED

- Found summary file: `.planning/phases/15-local-graph-metadata-retrieval-and-data-quality-review/15-03-SUMMARY.md`
- Verified commits exist: 5802af8, 2b2bff7, 8e2c3c4
- Verified key files exist: `src/ood/cli.py`, `tests/test_cli.py`, `README.md`
