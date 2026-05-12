---
phase: 04-ticket-intelligence
plan: 01
subsystem: ticket-intelligence
tags: [python, dataclasses, deterministic-rules, ticket-analysis]
requires:
  - phase: 02-core-rag-engine
    provides: SourceHit and ConfidenceScore query contracts
  - phase: 03-knowledge-management
    provides: source excerpts and metadata-aware retrieval inputs
provides:
  - Stable TicketAnalysis, TicketIdentifier, RoutingDecision, and CommandRisk dataclasses
  - Deterministic analyze_ticket() rule engine for intent, identifiers, routing, uncertainty, and command risk
affects: [04-ticket-intelligence, cli, rag-query]
tech-stack:
  added: []
  patterns: [frozen dataclasses with explicit to_dict, deterministic local rule engine]
key-files:
  created: [src/ood/ticket_intelligence.py, tests/test_ticket_intelligence.py]
  modified: [src/ood/models.py, tests/test_models.py]
key-decisions:
  - "Keep trusted ticket fields deterministic and local so Phase 4 works without Cloud LLM credentials."
  - "Represent intentional empty assessment and solution_steps in Plan 01 for later RAG/LLM enrichment."
patterns-established:
  - "Ticket analysis is an OOD-owned dataclass contract, not a LightRAG internal shape."
  - "Risk classification includes origin so CLI/JSON can distinguish ticket text from source excerpts."
requirements-completed: [TIC-01, TIC-03, TIC-04, TIC-05]
duration: 2min
completed: 2026-05-02
---

# Phase 04 Plan 01: Deterministic Ticket Intelligence Summary

**Deterministic ticket-analysis models and local rules for intent, routing, identifiers, uncertainties, and command-risk labels**

## Performance

- **Duration:** 2min
- **Started:** 2026-05-02T06:48:25Z
- **Completed:** 2026-05-02T06:50:39Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Added stable frozen dataclasses for nested ticket analysis JSON output.
- Implemented `analyze_ticket()` without LLM/API calls for deterministic operational fields.
- Covered intent, context-aware ID extraction, route selection, uncertainties, and command risk origins with tests.

## Task Commits

1. **Task 1: Add stable ticket analysis dataclasses** - `68625f8` (test), `531596f` (feat)
2. **Task 2: Implement deterministic analyzer rules** - `f118ef4` (test), `d29ca0e` (feat)

## Files Created/Modified
- `src/ood/models.py` - Adds `TicketAnalysis`, `TicketIdentifier`, `RoutingDecision`, and `CommandRisk` contracts.
- `src/ood/ticket_intelligence.py` - Implements deterministic local ticket analysis.
- `tests/test_models.py` - Locks model serialization behavior.
- `tests/test_ticket_intelligence.py` - Locks analyzer rules and safety labels.

## Decisions Made
- Keep trusted fields deterministic and local for privacy-safe MVP behavior.
- Leave `assessment=None` and `solution_steps=[]` in Plan 01 because Plan 02 owns retrieval/LLM enrichment.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs
- `src/ood/ticket_intelligence.py:45-46` intentionally returns `assessment=None` and `solution_steps=[]`; Plan 02 enriches those fields from `RagEngine.query()`/LLM output while preserving deterministic labels.

## Issues Encountered
- Initial command-risk implementation captured `status prüfen`; tightened read-only matching so the canonical command `status` is classified as `grün`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Ready for Plan 02 to add mandatory `QueryResult.analysis` and call `analyze_ticket()` from every query path.

## Self-Check: PASSED
- Verified created files exist: `src/ood/ticket_intelligence.py`, `tests/test_ticket_intelligence.py`.
- Verified commits exist: `68625f8`, `531596f`, `f118ef4`, `d29ca0e`.
- Verification passed: `uv run pytest tests/test_models.py tests/test_ticket_intelligence.py -q` → 12 passed.

---
*Phase: 04-ticket-intelligence*
*Completed: 2026-05-02*
