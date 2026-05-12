---
phase: 11-cli-grade-hybrid-retrieval-and-extractive-answer-synthesis
plan: 01
subsystem: retrieval
tags: [rag, hybrid-retrieval, diagnostics, local-first]
requires: [RAG-06, CLI-01]
provides: [retrieval_diagnostics, hybrid_semantic_lexical_scoring]
affects: [src/ood/models.py, src/ood/rag.py, tests/test_models.py, tests/test_rag.py]
tech_stack:
  added: []
  patterns: [frozen-dataclasses, deterministic-local-scoring]
key_files:
  created: []
  modified: [src/ood/models.py, src/ood/rag.py, tests/test_models.py, tests/test_rag.py]
decisions:
  - "Expose retrieval diagnostics as an additive QueryResult field while preserving existing top-level JSON fields."
  - "Use deterministic hybrid local fallback scoring with semantic, lexical, and exact-operational-token boost components."
metrics:
  duration: "part of phase execution"
  completed: 2026-05-04
---

# Phase 11 Plan 01: Hybrid Semantic+Lexical Retrieval Scoring and Diagnostics Summary

Hybrid local retrieval now ranks sources with semantic cosine, lexical exact-token coverage, and an explicit operational-token boost while serializing public diagnostics for each query.

## Completed Tasks

1. Added `RetrievalDiagnostics` and `SourceScoreBreakdown` dataclasses and attached diagnostics to `QueryResult.to_dict()`.
2. Replaced vector-only local fallback ranking with hybrid semantic+lexical scoring, clamped top-5 results, and per-source score breakdowns.

## Verification

- `uv run pytest tests/test_models.py tests/test_rag.py tests/test_cli.py -q` — 59 passed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Critical Functionality] Kept older QueryResult constructors compatible**
- **Found during:** Task 1
- **Issue:** Existing tests and CLI fakes instantiate `QueryResult` directly.
- **Fix:** Added a default diagnostics factory so old call sites remain valid while JSON gains diagnostics.
- **Files modified:** `src/ood/models.py`, `tests/test_models.py`, `tests/test_cli.py`
- **Commit:** `a391995`

## Known Stubs

None.

## Self-Check: PASSED

- Found modified files committed in implementation commit `a391995`.
- Targeted verification passed with 59 tests.
