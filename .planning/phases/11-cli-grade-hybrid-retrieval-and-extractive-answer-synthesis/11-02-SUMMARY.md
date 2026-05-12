---
phase: 11-cli-grade-hybrid-retrieval-and-extractive-answer-synthesis
plan: 02
subsystem: answer-synthesis
tags: [rag, extractive-answer, local-first, privacy]
requires: [ANS-01, CLI-01]
provides: [local_extractive_answer, cited_evidence_answer]
affects: [src/ood/rag.py, tests/test_rag.py]
tech_stack:
  added: []
  patterns: [deterministic-extraction, cited-evidence]
key_files:
  created: []
  modified: [src/ood/rag.py, tests/test_rag.py]
decisions:
  - "Generate default no-Cloud answers from cited source excerpts rather than Cloud LLM synthesis."
  - "Enrich only assessment, conservative solution steps, and mode for local extractive analysis while preserving deterministic trusted labels."
metrics:
  duration: "part of phase execution"
  completed: 2026-05-04
---

# Phase 11 Plan 02: Local Extractive Answer Synthesis from Top Sources Summary

Default local queries with retrieved sources now return a cited extractive answer and mark analysis as `local_extractive` without sending ticket content to a Cloud LLM.

## Completed Tasks

1. Added deterministic answer synthesis that selects concise evidence sentences from top-ranked excerpts and cites source ranks.
2. Added local analysis enrichment that preserves trusted deterministic routing, identifiers, uncertainties, and command-risk labels.

## Verification

- `uv run pytest tests/test_models.py tests/test_rag.py tests/test_cli.py -q` — 59 passed

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Grouped implementation with Plan 11-01 commit due overlapping dirty working tree**
- **Found during:** Phase continuation after user-approved inclusion of existing overlapping changes.
- **Issue:** `src/ood/rag.py` carried both hybrid retrieval and extractive answer changes in the same worktree state.
- **Fix:** Verified both behaviors together and documented the grouping; implementation is included in commit `a391995`.
- **Files modified:** `src/ood/rag.py`, `tests/test_rag.py`
- **Commit:** `a391995`

## Known Stubs

None.

## Self-Check: PASSED

- Extractive synthesis is implemented in `src/ood/rag.py` and covered by targeted retrieval tests.
- Targeted verification passed with 59 tests.
