---
phase: 02-core-rag-engine
plan: 01
subsystem: rag-foundation
tags: [python, uv, lightrag, sentence-transformers, openai, dataclasses, testing]

requires:
  - phase: 01-foundation-cli
    provides: uv Python package, strict test tooling, Settings path/credential contract, CLI JSON conventions
provides:
  - LightRAG and local semantic embedding runtime dependencies resolved through uv
  - OpenAI-compatible runtime package for credential-backed LightRAG helpers
  - Stable OOD-owned IndexResult, SourceHit, ConfidenceScore, QueryResult, and IndexMissingError contracts
affects: [02-core-rag-engine, cli-json-contract, rag-service]

tech-stack:
  added: [lightrag-hku==1.4.15, sentence-transformers==5.4.1, numpy==2.4.4, openai==2.33.0]
  patterns: [frozen dataclasses with explicit to_dict serialization, OOD-owned public result contracts]

key-files:
  created: [src/ood/models.py, tests/test_models.py]
  modified: [pyproject.toml, uv.lock]

key-decisions:
  - "Keep LightRAG internals behind OOD-owned frozen dataclasses before service and CLI integration."
  - "Use environment markers so NumPy 2.4.4 is installed on Python 3.11+ while preserving project Python 3.10 resolution compatibility."

patterns-established:
  - "Public RAG result objects expose stable to_dict() payloads instead of LightRAG raw structures."
  - "Source paths in query results are caller-provided relative strings; only IndexResult.storage_dir serializes a Path."

requirements-completed: [RAG-03, RAG-04, RAG-05]

duration: 5min 2s
completed: 2026-05-01
---

# Phase 02 Plan 01: Add LightRAG Dependencies and Stable RAG Result Models Summary

**LightRAG runtime foundation with local embeddings/OpenAI adapter packages and stable OOD-owned JSON result contracts**

## Performance

- **Duration:** 5min 2s
- **Started:** 2026-05-01T12:49:45Z
- **Completed:** 2026-05-01T12:54:47Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added the Phase 2 RAG dependency stack: `lightrag-hku==1.4.15`, `sentence-transformers==5.4.1`, `numpy==2.4.4`, and `openai==2.33.0`.
- Verified LightRAG, local embedding, NumPy, OpenAI, and `lightrag.llm.openai.openai_complete_if_cache` imports without any real secrets.
- Created frozen dataclass contracts for indexing/query results and tests that lock the stable CLI JSON fields required by D-14/D-15.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Phase 2 RAG runtime dependencies** - `88a895b` (chore)
2. **Task 2 RED: Create stable RAG result models tests** - `c93e90b` (test)
3. **Task 2 GREEN: Create stable RAG result models** - `dd807ff` (feat)

_Note: Task 2 followed TDD and therefore has separate test and implementation commits._

## Files Created/Modified

- `pyproject.toml` - Declares LightRAG, local embeddings, OpenAI-compatible runtime, and NumPy dependencies.
- `uv.lock` - Locks the resolved Phase 2 RAG dependency graph.
- `src/ood/models.py` - Exports `IndexResult`, `SourceHit`, `ConfidenceScore`, `QueryResult`, and `IndexMissingError`.
- `tests/test_models.py` - Verifies stable source, confidence, query, and index result serialization.

## Decisions Made

- OOD-owned dataclasses now define the public result boundary so downstream plans can normalize LightRAG responses without leaking retrieval internals.
- `IndexResult.storage_dir` intentionally serializes with `str(...)`; query source paths remain plain strings supplied by the source-normalization layer so absolute paths are not introduced here.
- NumPy uses a Python marker: `numpy==2.4.4` for Python 3.11+ and `numpy<2.4` for Python 3.10, preserving the project `>=3.10` contract while allowing the requested 2.4.4 runtime in the active environment.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Preserved Python 3.10 dependency resolution for NumPy**
- **Found during:** Task 1 (Add Phase 2 RAG runtime dependencies)
- **Issue:** `uv add ... numpy==2.4.4 ...` failed because NumPy 2.4.4 requires Python >=3.11 while the project declares `requires-python = ">=3.10"`.
- **Fix:** Added the requested `numpy==2.4.4` behind a Python 3.11+ marker and added a Python 3.10 fallback marker (`numpy<2.4`) so uv can resolve the full supported Python range.
- **Files modified:** `pyproject.toml`, `uv.lock`
- **Verification:** `uv lock --check` and the dependency import smoke test passed.
- **Committed in:** `88a895b`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary to satisfy both the requested dependency version on the active runtime and the established Python 3.10+ project contract. No scope creep.

## Issues Encountered

- No authentication gates or external-service setup were required.
- No secrets were configured, read, or committed.

## Known Stubs

None - no placeholder or UI-facing empty-data stubs were introduced in the files created or modified by this plan.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 02-02 can import the stable model contracts and wrap LightRAG indexing results without exposing storage internals.
- Plan 02-03 can build source scoring and confidence logic against the `SourceHit`, `ConfidenceScore`, and `QueryResult` contracts.

## Self-Check: PASSED

- Found all created/modified implementation files: `pyproject.toml`, `uv.lock`, `src/ood/models.py`, and `tests/test_models.py`.
- Found summary file: `.planning/phases/02-core-rag-engine/02-01-SUMMARY.md`.
- Found task commits: `88a895b`, `c93e90b`, and `dd807ff`.

---
*Phase: 02-core-rag-engine*
*Completed: 2026-05-01*
