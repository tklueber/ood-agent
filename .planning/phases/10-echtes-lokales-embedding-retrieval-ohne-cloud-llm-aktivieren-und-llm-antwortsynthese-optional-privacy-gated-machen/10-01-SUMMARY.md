---
phase: 10-echtes-lokales-embedding-retrieval-ohne-cloud-llm-aktivieren-und-llm-antwortsynthese-optional-privacy-gated-machen
plan: 01
subsystem: privacy
tags: [python, pydantic-settings, lightrag, rag, privacy]
requires:
  - phase: 02-core-rag-engine
    provides: RagEngine service layer and no-op LLM fallback contract
  - phase: 04-ticket-intelligence
    provides: QueryResult answer synthesis and deterministic ticket analysis contracts
provides:
  - Default-deny Cloud LLM approval setting
  - Derived can_use_cloud_llm permission contract
  - RagEngine gating for non-noop LLM functions, mix mode, and answer synthesis
affects: [local-retrieval, cli-diagnostics, documentation]
tech-stack:
  added: []
  patterns: [explicit privacy approval gate, credential detection separated from content-send permission]
key-files:
  created: []
  modified: [src/ood/config.py, src/ood/rag.py, tests/test_config.py, tests/test_rag.py]
key-decisions:
  - "Separate credential presence from Cloud LLM permission by keeping has_llm_credentials diagnostic-only and adding can_use_cloud_llm for any content-send path."
  - "Keep credentials-without-approval on retrieval-only/no-op LLM paths so configured secrets alone never enable answer synthesis."
patterns-established:
  - "Use Settings.can_use_cloud_llm for any path that could send ticket or knowledge content to a Cloud LLM."
  - "Use Settings.has_llm_credentials only for diagnostics and credential presence reporting."
requirements-completed: [LOCAL-RET-01, PRIV-01]
duration: 13min
completed: 2026-05-04
---

# Phase 10 Plan 01: Cloud LLM Privacy Gate Summary

**Default-deny Cloud LLM synthesis gate with credentials separated from explicit privacy approval across settings and RagEngine**

## Performance

- **Duration:** 13 min
- **Started:** 2026-05-04T17:22:34Z
- **Completed:** 2026-05-04T17:35:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Added `allow_cloud_llm: bool = False` and `can_use_cloud_llm` to the settings contract.
- Updated RagEngine query mode selection, answer synthesis, confidence rationale, local fallback selection, and LLM function building to use the explicit permission gate.
- Added TDD coverage proving credentials alone are insufficient while explicit approval plus credentials enables Cloud LLM paths.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add default-deny Cloud LLM approval setting** - `b66ca34` (test), `6896f58` (feat)
2. **Task 2: Use privacy approval for every non-noop LLM path** - `03b337e` (test), `b571691` (feat)

_Note: TDD tasks produced test → feat commits._

## Files Created/Modified

- `src/ood/config.py` - Adds `allow_cloud_llm` and `can_use_cloud_llm`.
- `src/ood/rag.py` - Uses `can_use_cloud_llm` for every Cloud LLM-enabling path.
- `tests/test_config.py` - Covers default-deny, credential detection, and explicit approval behavior.
- `tests/test_rag.py` - Covers credentials-without-approval no-op indexing and retrieval-only query behavior.

## Decisions Made

- `has_llm_credentials` remains available for diagnostics/backwards-compatible credential detection, but is no longer enough to enable Cloud LLM content paths.
- `can_use_cloud_llm` is the single permission contract for Cloud LLM usage in RagEngine.

## Deviations from Plan

None - plan executed as written.

## Issues Encountered

- TDD RED for Task 1 initially included `.env.example` documentation coverage; this was deferred back to Plan 10-03 so Plan 10-01 only changes its planned settings/RAG files.

## Known Stubs

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 10-02 can build local embedding fallback retrieval on top of a clear default no-Cloud permission boundary.
- Plan 10-03 can expose `can_use_cloud_llm` in CLI diagnostics and document the opt-in environment variable.

---
*Phase: 10-echtes-lokales-embedding-retrieval-ohne-cloud-llm-aktivieren-und-llm-antwortsynthese-optional-privacy-gated-machen*
*Completed: 2026-05-04*

## Self-Check: PASSED

- Verified modified files exist: `src/ood/config.py`, `src/ood/rag.py`, `tests/test_config.py`, `tests/test_rag.py`.
- Verified task commits exist: `b66ca34`, `6896f58`, `03b337e`, `b571691`.
