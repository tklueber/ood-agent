---
phase: 13-evaluation-service-and-cli-reporting
plan: 02
subsystem: evaluation
tags: [evaluation, eval-report, json-schema, serialization, tdd, wire-contract]
requires:
  - phase: 13-evaluation-service-and-cli-reporting
    provides: EvalRunResult, EvalRunMeta, EvalRunSummary, EvalCaseResult, SCHEMA_VERSION (Plan 01)
provides:
  - build_json_report(EvalRunResult) -> dict mapping to the D-05 locked wire schema
  - dump_json_report(EvalRunResult, *, indent=2) -> str UTF-8 JSON string
  - schema_version=1 invariant at top level and inside meta
  - llm_used propagated at meta / summary / per-case levels (D-07)
  - Skipped cases preserved in `cases` with null metrics (D-08)
  - Errored cases preserved in `cases` with stacktrace snippet (D-10)
affects: [phase-13-plan-03-cli, evaluation-reporting, skill-integration]
tech-stack:
  added: []
  patterns: [pure-serializer-no-formatting, single-source-wire-schema, locked-key-order, ensure-ascii-false-for-german-strings]
key-files:
  created:
    - src/ood/eval_report.py
    - tests/test_eval_report.py
  modified: []
key-decisions:
  - "Single source of truth for JSON: both stdout (`--json`) and file output (`--out`) in Plan 03 import `build_json_report`/`dump_json_report` from this module — there is no `--json` vs `--json-full` split (D-05)."
  - "Builder is data-only: metric dicts (`Hit@1`, `mrr`, `intent_accuracy`) flow through unchanged from `*.to_dict()`; no German user-facing strings are introduced here (D-04 — Plan 03 owns the human formatter)."
  - "Top-level key order locked to `schema_version, meta, summary, cases`; covered by an explicit test so reorderings produce a regression-visible failure."
  - "Skipped and errored cases keep their slot in `cases` (not filtered) and serialize their per-case metric dicts as JSON `null` rather than omitting the keys, so consumers can rely on a stable set of per-case fields."
patterns-established:
  - "Pure serializer pattern: the report builder consumes typed dataclasses, converts tuples to lists / leaves dicts intact, and never invokes formatting or rendering. Plan 03's human formatter will run alongside this — never inside it."
  - "Locked top-level key order via explicit test: `test_build_json_report_top_level_key_order_is_locked` asserts the `dict.keys()` sequence so accidental reorderings of `_build_meta`/`_build_summary`/`_build_case` calls in `build_json_report` are caught at test time."
  - "UTF-8 invariant for German strings: `dump_json_report` always passes `ensure_ascii=False`; a regression test asserts that `Bestanden`/`geprüft` appear verbatim in the raw string and that `\\u00fc` does not."
requirements-completed: [EVAL-06, EVAL-07]
duration: 2min
completed: 2026-05-11
---

# Phase 13 Plan 02: JSON Report Serializer Summary

**Pure-data builder that maps the typed `EvalRunResult` produced by Plan 01 into the D-05 locked wire schema, with `llm_used` mirrored at every level, skipped/errored cases preserved with null metrics, and German strings serialized verbatim via `ensure_ascii=False`.**

## Performance

- **Duration:** ~2min
- **Started:** 2026-05-11T08:08:42Z
- **Completed:** 2026-05-11T08:10:52Z
- **Tasks:** 1 (TDD)
- **Files created:** 2
- **Files modified:** 0
- **Tests added:** 14 (all in `tests/test_eval_report.py`)
- **Full project suite after Plan 02:** 157 passed (up from 143 after Plan 01)

## Accomplishments

- `build_json_report(result: EvalRunResult) -> dict[str, Any]` returns a plain dict with the locked top-level keys (`schema_version`, `meta`, `summary`, `cases`) in that exact order. The top-level `schema_version` is the module-level `SCHEMA_VERSION` literal (1); `meta.schema_version` mirrors `EvalRunMeta.schema_version`.
- `dump_json_report(result: EvalRunResult, *, indent: int | None = 2) -> str` emits `json.dumps(..., ensure_ascii=False, indent=indent, sort_keys=False)` so German strings (`Bestanden`, `geprüft`, ...) round-trip verbatim and key order is preserved.
- `meta` dict contains exactly the nine fields documented in CONTEXT.md D-05 (`schema_version`, `run_started_at`, `run_finished_at`, `llm_used`, `retrieval_backend`, `dataset`, `dataset_path`, `dataset_hash`, `command_args`). `command_args` is materialized as a `list[str]` for JSON compatibility.
- `summary` dict contains the nine aggregate fields (`case_count_total`, `case_count_aggregated`, `passed_count`, `failed_count`, `skipped_count`, `errored_count`, `llm_used`, `retrieval`, `ticket_intelligence`). The two metric dicts are passed through as-is (`Hit@1`, `mrr`, `intent_accuracy`, ...) — no renames.
- Each `cases[i]` entry contains the 13 documented fields (`case_id`, `query`, `status`, `skip_reason`, `error`, `llm_used`, `expected_sources`, `forbidden_sources`, `actual_sources`, `expected_llm_answer`, `retrieval_metrics`, `ticket_metrics`, `query_result`). Tuples (`expected_sources`, `forbidden_sources`, `actual_sources`) are converted to lists; per-source dicts are copied.
- D-07 enforced: `meta.llm_used`, `summary.llm_used`, and `cases[i].llm_used` are always present and independently controlled (covered by `test_build_json_report_propagates_llm_used_at_three_levels`).
- D-08 enforced: a skipped case keeps `status="skipped"`, `skip_reason="llm_required"`, and `retrieval_metrics`/`ticket_metrics`/`query_result` as JSON `null`; `actual_sources` is `[]`. Aggregation exclusion stays the runner's responsibility.
- D-10 enforced: an errored case keeps `status="errored"` and its stacktrace snippet survives the JSON round-trip in `error`.
- The builder is the single source of truth: Plan 03 will import `build_json_report` / `dump_json_report` directly — no second serializer.

## Public API (consumed by Plan 03)

```python
def build_json_report(result: EvalRunResult) -> dict[str, Any]:
    """Returns a plain dict matching the D-05 wire schema. Top-level keys
    are emitted in order: schema_version, meta, summary, cases."""

def dump_json_report(result: EvalRunResult, *, indent: int | None = 2) -> str:
    """json.dumps(build_json_report(result), ensure_ascii=False,
    indent=indent, sort_keys=False). Used by both stdout and --out."""
```

Both symbols are exported via `src/ood/eval_report.__all__`.

## Task Commits

1. **Task 1: Implement `build_json_report` serializer mapping EvalRunResult to the locked wire schema** — `e2d90cb` (test), `8f8893c` (feat)

_TDD: RED commit added 14 failing tests; GREEN commit shipped the serializer that makes them pass without further iteration._

## Files Created / Modified

- `src/ood/eval_report.py` (created, 112 lines) — `build_json_report`, `dump_json_report`, and three private helpers `_build_meta`, `_build_summary`, `_build_case`. Module docstring documents the schema invariants (D-05, D-07, D-08, D-10) so future maintainers see the locked contract before reading code.
- `tests/test_eval_report.py` (created, 14 tests) — schema shape, top-level key order, `llm_used` at three levels, skipped/errored isolation, UTF-8 German strings, `command_args` list serialization, and `dump_json_report` indent / compact modes.

## Wire Schema — Canonical Example

Exact `dump_json_report(result, indent=2)` output for a 1-passed / 1-skipped / 1-errored run, for Plan 03 to use as the human-formatter mirror reference:

```json
{
  "schema_version": 1,
  "meta": {
    "schema_version": 1,
    "run_started_at": "2026-05-10T16:39:04Z",
    "run_finished_at": "2026-05-10T16:39:42Z",
    "llm_used": false,
    "retrieval_backend": "local_vector_graph_index",
    "dataset": "mock-v1",
    "dataset_path": "evaluation/datasets/mock-v1.json",
    "dataset_hash": "a1b2c3d4e5f60000000000000000000000000000000000000000000000000000",
    "command_args": [
      "eval",
      "run",
      "--dataset",
      "evaluation/datasets/mock-v1.json"
    ]
  },
  "summary": {
    "case_count_total": 3,
    "case_count_aggregated": 1,
    "passed_count": 1,
    "failed_count": 0,
    "skipped_count": 1,
    "errored_count": 1,
    "llm_used": false,
    "retrieval": {
      "case_count": 1,
      "Hit@1": 1.0,
      "Hit@3": 1.0,
      "Hit@5": 1.0,
      "mrr": 1.0,
      "source_recall": 1.0,
      "forbidden_source_rate": 0.0
    },
    "ticket_intelligence": {
      "case_count": 1,
      "intent_accuracy": 1.0,
      "routing_accuracy": 1.0,
      "identifier_recall": 1.0,
      "command_risk_accuracy": 1.0,
      "uncertainty_accuracy": 1.0
    }
  },
  "cases": [
    {
      "case_id": "case-1",
      "query": "Police MOCK-POL-1001 bricht beim Login ab.",
      "status": "passed",
      "skip_reason": null,
      "error": null,
      "llm_used": false,
      "expected_sources": ["ticket/mock-pol-1001.md"],
      "forbidden_sources": [],
      "actual_sources": [
        {"path": "ticket/mock-pol-1001.md", "score": 0.92}
      ],
      "expected_llm_answer": null,
      "retrieval_metrics": {
        "case_id": "case-1",
        "Hit@1": true,
        "Hit@3": true,
        "Hit@5": true,
        "mrr": 1.0,
        "source_recall": 1.0,
        "forbidden_hit": false,
        "forbidden_hit_paths": [],
        "first_relevant_rank": 1
      },
      "ticket_metrics": {
        "case_id": "case-1",
        "intent_match": true,
        "routing_match": true,
        "identifier_recall": 1.0,
        "command_risk_accuracy": 1.0,
        "uncertainty_match": true,
        "missing_identifiers": [],
        "missing_command_risks": [],
        "missing_uncertainties": []
      },
      "query_result": {
        "query": "Police MOCK-POL-1001 bricht beim Login ab.",
        "answer": "Antwort aus Excerpts.",
        "confidence": {"score": 0.92, "label": "hoch"},
        "sources": [{"path": "ticket/mock-pol-1001.md", "score": 0.92}],
        "llm_used": false,
        "status": "answered",
        "analysis": {"intent": "Problem", "route": "weiterleiten Policen"},
        "retrieval_diagnostics": {"backend": "local_vector_graph_index"}
      }
    },
    {
      "case_id": "case-2",
      "query": "Bitte Cloud-LLM Antwort liefern.",
      "status": "skipped",
      "skip_reason": "llm_required",
      "error": null,
      "llm_used": false,
      "expected_sources": ["ticket/mock-pol-2002.md"],
      "forbidden_sources": [],
      "actual_sources": [],
      "expected_llm_answer": "Erwartete LLM-Antwort.",
      "retrieval_metrics": null,
      "ticket_metrics": null,
      "query_result": null
    },
    {
      "case_id": "case-3",
      "query": "Diese Query bringt RagEngine zum Absturz.",
      "status": "errored",
      "skip_reason": null,
      "error": "Traceback (most recent call last):\n  File ...\nRuntimeError: boom",
      "llm_used": false,
      "expected_sources": ["ticket/mock-pol-3003.md"],
      "forbidden_sources": [],
      "actual_sources": [],
      "expected_llm_answer": null,
      "retrieval_metrics": null,
      "ticket_metrics": null,
      "query_result": null
    }
  ]
}
```

## Test Catalogue

All 14 tests live in `tests/test_eval_report.py`. The first 11 mirror the plan's required-tests list; the final 3 are additional contract guards.

| #   | Test                                                                | Covers                                |
| --- | ------------------------------------------------------------------- | ------------------------------------- |
| 1   | `test_build_json_report_returns_top_level_schema_version_1`         | top-level and meta schema_version = 1 |
| 2   | `test_build_json_report_meta_contains_required_fields`              | meta key set (9 keys, exact match)    |
| 3   | `test_build_json_report_summary_contains_required_fields`           | summary key set (9 keys, exact match) |
| 4   | `test_build_json_report_case_contains_required_fields`              | case key set (13 keys, exact match)   |
| 5   | `test_build_json_report_propagates_llm_used_at_three_levels`        | D-07 (meta + summary + case)          |
| 6   | `test_build_json_report_skipped_case_has_null_metrics`              | D-08 (status=skipped, null payloads)  |
| 7   | `test_build_json_report_errored_case_includes_error_field`          | D-10 (status=errored, stacktrace)     |
| 8   | `test_build_json_report_command_args_serialized_as_list`            | tuple → list for command_args         |
| 9   | `test_build_json_report_actual_sources_preserves_order_and_score`   | per-case source ordering preserved    |
| 10  | `test_dump_json_report_emits_valid_utf8_json`                       | ensure_ascii=False, German strings    |
| 11  | `test_build_json_report_case_count_aggregated_excludes_skipped...`  | summary count fields end-to-end       |
| 12  | `test_build_json_report_top_level_key_order_is_locked`              | top-level dict key order              |
| 13  | `test_build_json_report_dump_uses_indent_two_by_default`            | dump default indent=2                 |
| 14  | `test_build_json_report_dump_allows_compact_output`                 | dump indent=None compact mode         |

## Decisions Made

- **Single schema, single builder.** No `--json` vs `--json-full` split; same payload feeds stdout and `--out` in Plan 03. This kills schema drift before it can start.
- **Pass metric dicts through unchanged.** `RetrievalCaseMetrics.to_dict()` already produces English-keyed JSON (`Hit@1`, `mrr`, `forbidden_hit`); same for `TicketIntelligenceCaseMetrics.to_dict()`. Re-keying here would create two source-of-truth places. Plan 03 maps English JSON keys to German display strings inside the human formatter only.
- **`null` instead of key omission for skipped/errored payloads.** A consumer that walks `cases[i].retrieval_metrics` should always find the key; `None` is unambiguous, missing keys are not. The test suite enforces this explicitly.
- **`sort_keys=False` is the default for `dump_json_report`.** The wire schema relies on a stable top-level ordering (`schema_version`, `meta`, `summary`, `cases`) that downstream skill consumers can rely on for diff-friendly output.
- **Locked top-level key order via test.** Adding a fourth call inside `build_json_report` without updating the test will fail visibly — the order is part of the contract.

## Deviations from Plan

None — Plan executed exactly as written. The plan listed 11 required tests; this implementation adds 3 additional contract guards (top-level key order, default indent, compact mode) that did not exist in the plan but cost nothing and tighten the contract for Plan 03. No code changes outside `src/ood/eval_report.py` and `tests/test_eval_report.py`.

## Known Stubs

None. `build_json_report` is fully wired against the real `EvalRunResult` produced by Plan 01's `EvalRunner.run()`. Every code path is exercised by the test suite.

## Issues Encountered

None. The RED step produced a clean `ModuleNotFoundError`, and the GREEN implementation passed all 14 tests on first run. No auto-fix attempts were needed.

## Auth Gates

None — the JSON serializer has no external dependencies. It pure-functions over typed dataclasses.

## User Setup Required

None. Importing `ood.eval_report` requires no environment variables, credentials, or configuration beyond the existing Plan 01 dependencies.

## Verification

- `uv run pytest tests/test_eval_report.py -x` → **14 passed**
- `uv run pytest tests/test_eval_report.py tests/test_eval_runner.py -q` → **31 passed**
- `uv run pytest -q` → **157 passed** (full project suite, up from 143 after Plan 01)
- `grep -q "def build_json_report" src/ood/eval_report.py` → ok
- `grep -q "def dump_json_report" src/ood/eval_report.py` → ok
- `grep -q "schema_version" src/ood/eval_report.py` → ok
- `grep -q "ensure_ascii=False" src/ood/eval_report.py` → ok
- `grep -q "from ood.eval_runner import" src/ood/eval_report.py` → ok
- `uv run python -c "from ood.eval_report import build_json_report, dump_json_report; print('ok')"` → `ok`
- Targeted `-k` checks for D-07, D-08, D-10, schema_version=1, and UTF-8 → **5 passed**

## Next Plan Readiness

**Plan 03 (CLI for `ood eval run` / `ood eval cases`):**

- Import `build_json_report` and `dump_json_report` from `ood.eval_report`; do not re-implement serialization.
- For `--json` flag → call `dump_json_report(result)` and write to stdout.
- For `--out <path>` flag → call `dump_json_report(result)` and `Path(path).write_text(..., encoding="utf-8")`. Same string both places.
- For the German human formatter (the `--json`-less default path) → build a separate renderer that consumes `EvalRunResult` directly (not the JSON dict); map English metric keys (`Hit@1`, `mrr`, `intent_accuracy`, ...) to German display labels at the formatter boundary only.
- Use the canonical example above as the visual mirror reference: every field that appears in the JSON should have a corresponding line in the German human output (or a deliberate omission).
- The `llm_used` marker in the human header (D-07, `»LLM«` prefix when true) reads `meta.llm_used` from the dataclass directly — the JSON builder is not on the human-rendering path.

## Self-Check: PASSED

Files exist:

- `src/ood/eval_report.py` → FOUND
- `tests/test_eval_report.py` → FOUND
- `.planning/phases/13-evaluation-service-and-cli-reporting/13-02-SUMMARY.md` → FOUND (this file)

Commits exist in `git log --oneline -5`:

- `e2d90cb` (test/RED Task 1) → FOUND
- `8f8893c` (feat/GREEN Task 1) → FOUND

---
*Phase: 13-evaluation-service-and-cli-reporting*
*Completed: 2026-05-11*
