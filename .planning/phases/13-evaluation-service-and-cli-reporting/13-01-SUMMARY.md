---
phase: 13-evaluation-service-and-cli-reporting
plan: 01
subsystem: evaluation
tags: [evaluation, eval-runner, cloud-llm-gate, privacy, orchestration, pytest, tdd]
requires:
  - phase: 12-evaluation-dataset-and-metric-core
    provides: EvaluationDataset, EvaluationCase, evaluate_retrieval_case, evaluate_ticket_intelligence_case
  - phase: 02-core-rag-engine
    provides: public RagEngine.query() contract and QueryResult dataclass
  - phase: 10-echtes-lokales-embedding-retrieval-ohne-cloud-llm-aktivieren-und-llm-antwortsynthese-optional-privacy-gated-machen
    provides: Settings.has_llm_credentials and the privacy-gated Cloud-LLM activation contract
provides:
  - EvalRunner orchestration service with credentials-only Cloud-LLM gate
  - EvalCaseResult, EvalRunSummary, EvalRunMeta, EvalRunResult typed dataclasses
  - Effective-Settings forging via Settings.model_copy so RagEngine's internal privacy gate flips True end-to-end when credentials exist
  - IndexMissingError propagation (D-09) and per-case crash isolation (D-10)
  - Optional EvaluationCase.expected_llm_answer field for skip-on-no-llm (D-08)
  - Settings.eval_dataset_path bound to OOD_EVAL_DATASET env var
affects: [phase-13-plan-02-json-report, phase-13-plan-03-cli, evaluation-reporting]
tech-stack:
  added: []
  patterns: [effective-settings-forging, public-contract-dispatch, typed-orchestration-result, exception-layered-isolation, regression-proof-source-inspection]
key-files:
  created:
    - src/ood/eval_runner.py
    - tests/test_eval_runner.py
  modified:
    - src/ood/config.py
    - src/ood/evaluation.py
    - tests/test_config.py
    - tests/test_evaluation.py
key-decisions:
  - "Eval activates the Cloud-LLM path on Settings.has_llm_credentials alone — never on the privacy ENV flag — and forges effective Settings so RagEngine's internal privacy gate flips True end-to-end without mutating the caller's Settings (D-06)."
  - "IndexMissingError raised by RagEngine.query bubbles out of EvalRunner.run() unchanged so the CLI can map it to exit code 1 (D-09); any other per-case exception is captured as status='errored' with a stacktrace snippet and the run continues (D-10)."
  - "Cases declaring expected_llm_answer are reported as status='skipped' with skip_reason='llm_required' when credentials are absent and are excluded from aggregated metrics (D-08)."
  - "The single legitimate reference to allow_cloud_llm in eval_runner.py is inside _engine_settings; a regression-proof source-inspection test enforces this and forbids any reference to the composite privacy property anywhere in the module."
  - "Settings.eval_dataset_path uses pydantic AliasChoices to honor the documented OOD_EVAL_DATASET env var despite the OOD_ env_prefix that would otherwise expect OOD_EVAL_DATASET_PATH."
patterns-established:
  - "Effective-Settings forging: when business-logic and engine-internal gates diverge, derive an effective Settings via model_copy at the boundary rather than mutating shared state."
  - "Layered exception handling for case execution: re-raise hard errors (IndexMissingError) before a broad except so per-case crashes can be isolated without swallowing run-aborting conditions."
  - "Regression-proof gate checks via inspect.getsource: enforce that forbidden identifiers do not appear outside a single helper, catching accidental reintroduction during future refactors."
requirements-completed: [EVAL-02, EVAL-07]
duration: 25min
completed: 2026-05-11
---

# Phase 13 Plan 01: EvalRunner Orchestration Service Summary

**Typed eval orchestration that drives every EvaluationDataset case through the public RagEngine.query() contract, with credentials-only Cloud-LLM activation forged into effective Settings, IndexMissingError propagation, and per-case crash isolation.**

## Performance

- **Duration:** ~25min
- **Started:** 2026-05-11T07:40Z
- **Completed:** 2026-05-11T08:05Z
- **Tasks:** 2 (both TDD)
- **Files created:** 2
- **Files modified:** 4
- **Tests added:** 22 (17 EvalRunner + 3 expected_llm_answer + 2 eval_dataset_path)

## Accomplishments

- `EvalRunner.run(dataset, dataset_path, case_id=None, command_args=None)` dispatches every case through `engine.query()` exactly once via a single reused `RagEngine` instance.
- `_engine_settings(settings)` forges effective Settings (`settings.model_copy(update={"allow_cloud_llm": True})`) whenever credentials exist, without mutating the caller's Settings. This is the only location in `eval_runner.py` that references `allow_cloud_llm`, and the module never references the composite privacy property.
- D-06 divergence proved end-to-end: with `OOD_LLM_API_KEY=sk-...` set and `OOD_ALLOW_CLOUD_LLM=false`, `RagEngine.settings.can_use_cloud_llm` evaluates to True inside the engine without polluting the user-supplied Settings.
- D-08 skip handling: cases with `expected_llm_answer` are marked `status="skipped"` / `skip_reason="llm_required"` when credentials are absent, excluded from aggregated metrics and pass/fail counts.
- D-09 hard-error propagation: `IndexMissingError` from `engine.query` bubbles out of `run()` unchanged for downstream exit-1 mapping in Plan 03.
- D-10 per-case crash isolation: any other exception is captured as `status="errored"` with a 2000-char stacktrace snippet; the run continues for the remaining cases.
- Meta block carries `schema_version=1`, ISO-8601 UTC timestamps (`...Z` suffix, microseconds stripped), `dataset_hash` (sha256 of dataset file bytes), `dataset_path`, `dataset`, `retrieval_backend` (first non-skipped case's `retrieval_diagnostics.backend`, defaulting to `"unknown"`), `llm_used`, and `command_args`.
- `EvaluationCase.expected_llm_answer: str | None` is parsed by `load_evaluation_dataset` via a new `_optional_str` helper: absent → `None`, present-and-blank → `EvaluationDatasetError`, valid → trimmed string. The existing `mock-v1` fixture still loads unchanged.
- `Settings.eval_dataset_path` defaults to `Path("evaluation/datasets/mock-v1.json")` and accepts `OOD_EVAL_DATASET=/path/...` via `pydantic.AliasChoices` so the documented short env-var name takes precedence over the prefix-expanded form.
- End-to-end smoke verified: running `EvalRunner(Settings()).run(load_evaluation_dataset(Path("evaluation/datasets/mock-v1.json")), dataset_path=...)` with a fake `RagEngine` exercises all four committed `mock-v1` cases and produces a valid `EvalRunResult`.

## Task Commits

1. **Task 1: Add Settings.eval_dataset_path and optional EvaluationCase.expected_llm_answer field** — `551f69b` (test), `86273a1` (feat)
2. **Task 2: Implement EvalRunner with skip/errored/llm_used handling, credential-only Cloud-LLM gate forged into effective Settings, and IndexMissingError propagation** — `8790d75` (test), `23a00f1` (feat)

_Note: TDD tasks have test → feat commits._

## Files Created / Modified

- `src/ood/eval_runner.py` (created) — `EvalRunner`, `EvalCaseResult`, `EvalRunSummary`, `EvalRunMeta`, `EvalRunResult`, `EvalRunnerError`, `_engine_settings` helper, and `SCHEMA_VERSION`.
- `tests/test_eval_runner.py` (created) — 17 EvalRunner tests covering happy/failed/skipped/errored, D-06 effective-Settings forging, D-09 propagation, D-10 isolation, dataset-hash + ISO timestamps, `case_id` filter, `EvalRunnerError`, `summary.llm_used` aggregation, retrieval-backend derivation, and a regression-proof source-inspection guard.
- `src/ood/config.py` (modified) — added `Settings.eval_dataset_path` with `Field(..., validation_alias=AliasChoices("OOD_EVAL_DATASET", "OOD_EVAL_DATASET_PATH", "eval_dataset_path"))`.
- `src/ood/evaluation.py` (modified) — added optional `EvaluationCase.expected_llm_answer` field and `_optional_str` parser helper.
- `tests/test_config.py` (modified) — added tests for `eval_dataset_path` default and `OOD_EVAL_DATASET` env binding.
- `tests/test_evaluation.py` (modified) — added tests for `expected_llm_answer` accept/default/reject paths.

## Public Types (consumed by Plans 02 and 03)

```python
@dataclass(frozen=True)
class EvalCaseResult:
    case_id: str
    query: str
    status: str  # "passed" | "failed" | "skipped" | "errored"
    skip_reason: str | None
    error: str | None
    llm_used: bool
    query_result: dict[str, Any] | None  # full QueryResult.to_dict()
    retrieval_metrics: dict[str, Any] | None
    ticket_metrics: dict[str, Any] | None
    expected_sources: tuple[str, ...]
    forbidden_sources: tuple[str, ...]
    actual_sources: tuple[dict[str, Any], ...]  # [{"path", "score"}, ...]
    expected_llm_answer: str | None

@dataclass(frozen=True)
class EvalRunSummary:
    case_count_total: int
    case_count_aggregated: int  # passed + failed only
    passed_count: int
    failed_count: int
    skipped_count: int
    errored_count: int
    llm_used: bool
    retrieval: dict[str, Any]            # RetrievalMetricsSummary.to_dict()
    ticket_intelligence: dict[str, Any]  # TicketIntelligenceMetricsSummary.to_dict()

@dataclass(frozen=True)
class EvalRunMeta:
    schema_version: int        # = 1
    run_started_at: str        # ISO-8601 UTC, "...Z"
    run_finished_at: str       # ISO-8601 UTC, "...Z"
    llm_used: bool
    retrieval_backend: str
    dataset: str               # EvaluationDataset.dataset (e.g. "mock-v1")
    dataset_path: str
    dataset_hash: str          # sha256 hex of dataset file bytes
    command_args: tuple[str, ...]

@dataclass(frozen=True)
class EvalRunResult:
    meta: EvalRunMeta
    summary: EvalRunSummary
    cases: tuple[EvalCaseResult, ...]
```

## Cloud-LLM Gate Divergence Anchor

The runner contains exactly one comment block referencing `allow_cloud_llm`, inside `_engine_settings`:

```python
@staticmethod
def _engine_settings(settings: Settings) -> Settings:
    # DELIBERATE DIVERGENCE from `ood query` (CONTEXT.md D-06):
    # Eval activates the Cloud-LLM path on credential availability alone.
    # RagEngine internally gates LLM usage on the Settings privacy
    # property (which requires both the privacy ENV approval AND
    # credentials), so we forge an effective Settings object in which
    # `allow_cloud_llm` is True whenever credentials exist. This is the
    # ONLY place in eval_runner.py that may reference `allow_cloud_llm`.
    # Business logic elsewhere consults `has_llm_credentials` exclusively.
    if settings.has_llm_credentials:
        return settings.model_copy(update={"allow_cloud_llm": True})
    return settings
```

`test_run_does_not_consult_allow_cloud_llm_in_business_logic` enforces this invariant by reading the module source, isolating the helper body, and asserting `allow_cloud_llm` does not appear outside it and the composite privacy property is absent everywhere.

## Pass/Fail Rule

A case is `"passed"` when **all** of the following hold; otherwise `"failed"`:

- `retrieval_metrics.hit_at_5 is True`
- `not retrieval_metrics.forbidden_hit`
- `ticket_metrics.intent_match is True`
- `ticket_metrics.routing_match is True`
- `ticket_metrics.identifier_recall == 1.0`
- `ticket_metrics.command_risk_accuracy == 1.0`
- `ticket_metrics.uncertainty_match is True`

Skipped and errored cases never produce per-case metric dicts and are excluded from `case_count_aggregated`.

## IndexMissingError Propagation Contract

`_run_case` uses a layered try/except: `except IndexMissingError: raise` precedes the broader `except Exception` block, so `IndexMissingError` bubbles out of `_run_case`, then out of `run()`, untouched. The runner does **not** convert it to `status="errored"`. The CLI (Plan 03) is responsible for catching it and mapping it to exit code 1.

## Decisions Made

- **D-06 enforcement strategy:** forge effective Settings via `model_copy` at the engine boundary rather than passing a separate "force_llm" flag through `RagEngine`. This keeps the divergence contained to `eval_runner.py` and leaves `RagEngine` semantics identical between eval and `ood query`.
- **OOD_EVAL_DATASET binding:** use `pydantic.AliasChoices` so the documented short env-var name survives despite the model's `env_prefix="OOD_"` (which would otherwise expect `OOD_EVAL_DATASET_PATH`). Falls back to the prefix-expanded form and the field name for completeness.
- **Engine reuse:** one `RagEngine` instance per `run()` call (per CONTEXT.md "engine reuse" discretion). Each `query()` is stateless w.r.t. the index.
- **command_args storage:** stored on `EvalRunMeta` as `tuple[str, ...]` (immutable) but exposed to JSON serialization as a list in downstream plans.

## Deviations from Plan

None — plan executed exactly as written. The only minor wording change was in the `_engine_settings` docstring: the original draft referenced the composite privacy property by name, which the regression-proof source-inspection test (test 9) deliberately forbids. The comment was rephrased to describe the property indirectly while preserving the intent.

## Known Stubs

None — `EvalRunner` is fully wired against the real `RagEngine.query()` contract and the `mock-v1` fixture.

## Issues Encountered

- `pydantic-settings` with `env_prefix="OOD_"` would by default bind `eval_dataset_path` to `OOD_EVAL_DATASET_PATH`, not the documented `OOD_EVAL_DATASET`. Fixed by attaching `validation_alias=AliasChoices(...)` to the field. Discovered immediately by the test, no production impact.
- The regression-proof source-inspection test forbids the literal string `allow_cloud_llm` outside `_engine_settings` (including in comments) and forbids the composite privacy-property string anywhere. The initial draft of the `run()` body had a clarifying comment that mentioned both — the comment was rephrased to satisfy the invariant without losing clarity.

## User Setup Required

None. EvalRunner is exercised purely with `Settings()` and a dataset path; no external service configuration is needed for the local/credentials-absent path. When credentials are present, the existing `OOD_LLM_API_KEY` and provider configuration apply unchanged.

## Verification

- `uv run pytest tests/test_eval_runner.py -q` → 17 passed
- `uv run pytest tests/test_evaluation.py tests/test_evaluation_metrics.py tests/test_evaluation_ticket_metrics.py tests/test_eval_runner.py -q` → 40 passed (Phase 12 + new runner suite)
- `uv run pytest -q` → 143 passed (full project suite, up from 121)
- `grep -q "class EvalRunner" src/ood/eval_runner.py` → ok
- `grep -q "DELIBERATE DIVERGENCE" src/ood/eval_runner.py` → ok
- `grep -q "_engine_settings" src/ood/eval_runner.py` → ok
- `grep -q "model_copy" src/ood/eval_runner.py` → ok
- `grep -q "except IndexMissingError" src/ood/eval_runner.py` → ok
- `! grep -q "can_use_cloud_llm" src/ood/eval_runner.py` → ok
- `OOD_EVAL_DATASET=/tmp/foo.json uv run python -c "..."` → `/tmp/foo.json`
- End-to-end run on committed `evaluation/datasets/mock-v1.json` produced `case_count_total=4`, `case_count_aggregated=4`, valid `dataset_hash`, `llm_used=False`, `retrieval_backend="local_vector_index"`.

## Next Plan Readiness

- **Plan 02 (JSON report builder):** can consume `EvalRunResult` directly — `meta`, `summary`, and `cases` already hold every field a versioned JSON schema needs, including full `QueryResult.to_dict()` per case, retrieval and ticket-intelligence metric dicts, and `actual_sources` with paths and scores.
- **Plan 03 (CLI):** can wire `ood eval run` to call `EvalRunner.run(...)`, surface `meta.llm_used` in the header, render `summary.passed/failed/skipped/errored` counts, format failure details from `cases` where `status == "failed"`, and exit `1` when `IndexMissingError` propagates out of `run()` or when dataset loading raises.

## Self-Check: PASSED

Files exist:
- `src/ood/eval_runner.py` → FOUND
- `tests/test_eval_runner.py` → FOUND

Commits exist in `git log --oneline -6`:
- `551f69b` (test Task 1) → FOUND
- `86273a1` (feat Task 1) → FOUND
- `8790d75` (test Task 2) → FOUND
- `23a00f1` (feat Task 2) → FOUND

---
*Phase: 13-evaluation-service-and-cli-reporting*
*Completed: 2026-05-11*
