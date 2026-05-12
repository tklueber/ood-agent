---
phase: 10-echtes-lokales-embedding-retrieval-ohne-cloud-llm-aktivieren-und-llm-antwortsynthese-optional-privacy-gated-machen
plan: 03
subsystem: cli-docs
tags: [typer, cli, privacy, documentation, env]
requires:
  - phase: 10-echtes-lokales-embedding-retrieval-ohne-cloud-llm-aktivieren-und-llm-antwortsynthese-optional-privacy-gated-machen
    provides: Plans 10-01 and 10-02 privacy gate plus local vector retrieval behavior
provides:
  - Verbose CLI diagnostics for Cloud LLM approval and usage
  - README workflow documentation for local embeddings and opt-in synthesis
  - Safe `.env.example` privacy gate template
affects: [operator-workflow, configuration, privacy-audit]
tech-stack:
  added: []
  patterns: [non-secret CLI diagnostics, JSON contract isolation]
key-files:
  created: []
  modified: [src/ood/cli.py, tests/test_cli.py, tests/test_config.py, README.md, .env.example]
key-decisions:
  - "Expose cloud_llm_allowed only in verbose human output while keeping JSON exactly QueryResult.to_dict()."
  - "Document OOD_ALLOW_CLOUD_LLM=false as the explicit privacy approval gate rather than implying credentials are enough."
patterns-established:
  - "CLI diagnostics may render non-secret settings decisions but must not add automation-only fields to JSON output."
  - "Tests that force local fallback monkeypatch embedding generation to avoid model-download noise in JSON assertions."
requirements-completed: [PRIV-01, PRIV-02, LOCAL-RET-02]
duration: 7min
completed: 2026-05-04
---

# Phase 10 Plan 03: CLI Diagnostics and Local-First Docs Summary

**Operators can audit Cloud LLM approval in verbose CLI output and follow README/.env guidance for local embeddings with opt-in synthesis**

## Performance

- **Duration:** 7 min
- **Started:** 2026-05-04T17:43:00Z
- **Completed:** 2026-05-04T17:50:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added `cloud_llm_allowed` to verbose human `ood query` diagnostics without leaking secrets.
- Preserved JSON query output as `QueryResult.to_dict()` with no CLI-only fields.
- Updated README and `.env.example` to explain local vector retrieval, default-deny Cloud LLM synthesis, and `OOD_ALLOW_CLOUD_LLM=false`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add privacy/local-retrieval query diagnostics** - `8be498a` (test), `6d027f9` (feat)
2. **Task 2: Document local embeddings and opt-in Cloud LLM synthesis** - `834e641` (docs)

## Files Created/Modified

- `src/ood/cli.py` - Threads `settings.can_use_cloud_llm` into verbose query diagnostics.
- `tests/test_cli.py` - Covers verbose diagnostics, JSON contract isolation, and deterministic local embedding test mocks.
- `tests/test_config.py` - Requires `.env.example` to document `OOD_ALLOW_CLOUD_LLM`.
- `README.md` - Documents local vector retrieval and opt-in Cloud LLM synthesis behavior.
- `.env.example` - Adds the explicit privacy approval gate with a safe false default.

## Decisions Made

- CLI output uses `cloud_llm_allowed` as a non-secret boolean so operators can distinguish approval from actual `llm_used` behavior.
- `.env.example` keeps the approval flag false by default and avoids real secrets, provider URLs, or production identifiers.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Avoided local embedding model output in CLI JSON tests**
- **Found during:** Task 2 verification
- **Issue:** Existing CLI mock-corpus tests forced the local fallback path and sentence-transformer model initialization emitted external model-loading output, corrupting JSON assertions.
- **Fix:** Monkeypatched `_encode_local_embeddings` in those tests so JSON output remains deterministic and no model download/progress output appears.
- **Files modified:** `tests/test_cli.py`
- **Verification:** `uv run pytest tests/test_cli.py -q` and `uv run pytest tests/test_cli.py tests/test_config.py tests/test_rag.py -q`
- **Committed in:** `834e641`

**Total deviations:** 1 auto-fixed (Rule 3 blocking)
**Impact on plan:** Kept verification deterministic without changing production behavior.

## Issues Encountered

- Hugging Face/model-loading warnings appeared in CLI JSON tests before the test boundary was mocked; resolved as a blocking test determinism issue.

## Known Stubs

- `.env.example:2` uses the word "placeholders" intentionally because the file is a safe template and must not contain real credentials.

## User Setup Required

None - Cloud LLM synthesis remains disabled unless the user explicitly sets `OOD_ALLOW_CLOUD_LLM=true` and provides credentials in `.env` or the environment.

## Next Phase Readiness

- Phase 10 goal is ready for verification: local vector retrieval is active by default and Cloud LLM synthesis is opt-in and auditable.

---
*Phase: 10-echtes-lokales-embedding-retrieval-ohne-cloud-llm-aktivieren-und-llm-antwortsynthese-optional-privacy-gated-machen*
*Completed: 2026-05-04*

## Self-Check: PASSED

- Verified modified files exist: `src/ood/cli.py`, `tests/test_cli.py`, `tests/test_config.py`, `README.md`, `.env.example`.
- Verified task commits exist: `8be498a`, `6d027f9`, `834e641`.
