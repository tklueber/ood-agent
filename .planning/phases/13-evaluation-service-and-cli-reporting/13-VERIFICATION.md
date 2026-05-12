---
phase: 13-evaluation-service-and-cli-reporting
verified: 2026-05-11T11:00:00Z
status: passed
score: 9/9 must-haves verified
---

# Phase 13: Evaluation Service and CLI Reporting Verification Report

**Phase Goal:** User can run local black-box evaluations through `RagEngine.query()` and consume reports in both human-readable and machine-readable forms.
**Verified:** 2026-05-11T11:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

Derived from the ROADMAP Success Criteria for Phase 13 (lines 320–331 of ROADMAP.md show generic eval criteria) and the union of `must_haves.truths` across plans 13-01, 13-02, 13-03.

| #   | Truth                                                                                                                                                  | Status     | Evidence                                                                                                                                          |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | User can run an evaluation that calls the public `RagEngine.query()` contract for each case (EVAL-02).                                                  | VERIFIED   | `src/ood/eval_runner.py:224` `query_result: QueryResult = engine.query(case.query)` inside the single `_run_case` dispatch path.                  |
| 2   | User can run `ood eval run` and `ood eval cases` Typer subcommands; help and German strings exposed.                                                    | VERIFIED   | `ood eval --help` shows `run` + `cases` subcommands; `eval_app = typer.Typer(name="eval", ...)` at `eval_cli.py:51`; `add_typer` at `cli.py:521`. |
| 3   | User can write structured JSON output with `schema_version=1`, dataset metadata, case results, metrics, paths, backend information, and `llm_used`.    | VERIFIED   | `eval_report.py` `build_json_report`/`dump_json_report`, top-level `schema_version=SCHEMA_VERSION=1`, `meta.llm_used` / `summary.llm_used` / per-case `llm_used` (D-07). |
| 4   | User can view concise CLI output with run status, core metrics, failed cases, and useful expected-vs-actual diagnostics in German.                      | VERIFIED   | `_emit_human_report` + `_emit_failed_case` + `_collect_mismatch_parts` in `eval_cli.py:238–429`; produces `OOD Evaluation`, `Cloud-LLM verwendet`, `Bestanden`, `Fehlgeschlagen`, `Fehlgeschlagene Fälle`, `Übersprungene Fälle`, `Fehler` sections. |
| 5   | User can run evaluations locally without Cloud LLM usage by default; every report explicitly shows `llm_used` (EVAL-07).                                | VERIFIED   | `EvalRunner` business-logic gate is `has_llm_credentials` only (eval_runner.py:135); `meta.llm_used` defaults to False and the `»LLM«` marker prefix is rendered only when True (eval_cli.py:257–260). |
| 6   | Cloud-LLM activation in eval is decided by `Settings.has_llm_credentials` only (deliberate D-06 divergence) and forges effective Settings via `model_copy`. | VERIFIED   | `_engine_settings` helper in `eval_runner.py:98–110`: `settings.model_copy(update={"allow_cloud_llm": True})` if credentials present; 0 references to `can_use_cloud_llm`, only 3 references to `allow_cloud_llm` (all in the helper / comment block). |
| 7   | Cases declaring `expected_llm_answer` skip with `skip_reason="llm_required"` when credentials are absent and are excluded from aggregation.             | VERIFIED   | `eval_runner.py:202–221` skip branch; `expected_llm_answer` field added to `EvaluationCase` (evaluation.py:40) and parsed by `_optional_str` (evaluation.py:111,122). |
| 8   | `IndexMissingError` from `RagEngine.query` propagates out of `EvalRunner.run()` and the CLI maps it to exit-1 with a German message (D-09).             | VERIFIED   | `eval_runner.py:225–227` `except IndexMissingError: raise`; `eval_cli.py:144–151` catches it and emits `"Kein Index gefunden. Bitte zuerst `ood index` ausführen."` to stderr with `typer.Exit(code=1)`. |
| 9   | `Settings.eval_dataset_path` is loaded from `OOD_EVAL_DATASET` env var with a deterministic default and overridable by `--dataset`.                     | VERIFIED   | `config.py:18–21` uses `AliasChoices("OOD_EVAL_DATASET", "OOD_EVAL_DATASET_PATH", "eval_dataset_path")`; smoke `OOD_EVAL_DATASET=/tmp/foo_test.json` → `/tmp/foo_test.json`; CLI override `eval_cli.py:124`. |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact                          | Expected                                                                                              | Status      | Details                                                                                                                                                                                |
| --------------------------------- | ----------------------------------------------------------------------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `src/ood/eval_runner.py`          | `class EvalRunner`, `_engine_settings`, dataclasses, `SCHEMA_VERSION=1`                                | VERIFIED    | 301 lines; all required classes + helper present; substantive; wired (imported by `eval_report.py` and `eval_cli.py`).                                                                  |
| `src/ood/eval_report.py`          | `build_json_report`, `dump_json_report`, `from ood.eval_runner import`, `ensure_ascii=False`            | VERIFIED    | 112 lines; both functions present; module docstring documents schema invariants D-05/D-07/D-08/D-10.                                                                                    |
| `src/ood/eval_cli.py`             | `eval_app` Typer sub-app with `run`/`cases`, German formatter, exit-code policy, IndexMissingError handler | VERIFIED  | 442 lines; both subcommands present; German strings (`Fehlgeschlagene Fälle`, `Übersprungene Fälle`, `»LLM«`, `Kein Index gefunden`); wired into `cli.py:519–521`.                       |
| `src/ood/cli.py`                  | `add_typer(eval_app, name="eval")` at bottom (deferred import)                                         | VERIFIED    | Line 519 `from ood.eval_cli import eval_app`; line 521 `app.add_typer(eval_app, name="eval")`.                                                                                          |
| `src/ood/config.py`               | `Settings.eval_dataset_path` bound to `OOD_EVAL_DATASET`                                               | VERIFIED    | Lines 18–21; `AliasChoices` honors short env var; smoke-tested.                                                                                                                          |
| `src/ood/evaluation.py`           | Optional `EvaluationCase.expected_llm_answer: str | None`                                              | VERIFIED    | Line 40 default `None`; parsed via `_optional_str` (line 122) and wired into `_parse_case` (line 111).                                                                                  |
| `tests/test_eval_runner.py`       | EvalRunner test suite                                                                                  | VERIFIED    | 17 tests, all passing. Note: gsd-tools flagged a missing `def test_eval_runner` substring pattern but the file legitimately uses `def test_run_…` naming — false-positive.             |
| `tests/test_eval_report.py`       | JSON serializer test suite                                                                             | VERIFIED    | 14 tests, all passing.                                                                                                                                                                  |
| `tests/test_eval_cli.py`          | CLI integration test suite                                                                             | VERIFIED    | 24 tests, all passing.                                                                                                                                                                  |

### Key Link Verification

Several gsd-tools checks were false-positives due to backslash-escaped regex patterns in plan frontmatter and source-file path heuristics (e.g. `src/ood/eval_runner.py::_engine_settings` treated as a separate file). Manual grep verification:

| From                                  | To                                                            | Via                                                              | Status      | Details                                                                                              |
| ------------------------------------- | ------------------------------------------------------------- | ---------------------------------------------------------------- | ----------- | ---------------------------------------------------------------------------------------------------- |
| `eval_runner.py`                       | `rag.py::RagEngine.query`                                     | `engine.query(case.query)`                                       | WIRED       | `eval_runner.py:224` `query_result: QueryResult = engine.query(case.query)`.                          |
| `eval_runner.py`                       | `config.py::Settings.has_llm_credentials`                     | credentials-only LLM activation gate                              | WIRED       | `eval_runner.py:108,135` reference `has_llm_credentials`.                                              |
| `eval_runner.py::_engine_settings`     | `config.py::Settings (model_copy)`                            | `settings.model_copy(update={'allow_cloud_llm': True})`           | WIRED       | `eval_runner.py:109` exact pattern present.                                                            |
| `eval_runner.py::_run_case`            | `models.py::IndexMissingError`                                | re-raise before generic except                                    | WIRED       | `eval_runner.py:225–227` `except IndexMissingError: raise`.                                            |
| `eval_runner.py`                       | `evaluation_metrics.py`                                       | `evaluate_retrieval_case + summarize_retrieval_metrics`           | WIRED       | Both imported at top of file (lines 13–17) and invoked at 250 / 168.                                  |
| `eval_runner.py`                       | `evaluation_ticket_metrics.py`                                | `evaluate_ticket_intelligence_case + summarize_ticket_intelligence_metrics` | WIRED | Lines 18–22 imports; invoked at 251 / 169.                                                              |
| `eval_report.py`                       | `eval_runner.py::EvalRunResult`                               | `build_json_report` consumes `EvalRunResult`                      | WIRED       | `eval_report.py:29` `from ood.eval_runner import EvalCaseResult, EvalRunResult, SCHEMA_VERSION`.       |
| `eval_report.py`                       | `json.dumps`                                                  | `ensure_ascii=False, sort_keys=False`                              | WIRED       | `eval_report.py:56–61` `return json.dumps(..., ensure_ascii=False, indent=indent, sort_keys=False)`.   |
| `eval_cli.py`                          | `eval_runner.py::EvalRunner`                                  | `EvalRunner(settings).run(...)`                                   | WIRED       | `eval_cli.py:138` `result = EvalRunner(settings).run(...)`.                                            |
| `eval_cli.py`                          | `eval_report.py::build_json_report`                            | `dump_json_report` used for stdout & file                          | WIRED       | `eval_cli.py:68` import; lines 163, 166 invocations.                                                   |
| `cli.py`                               | `eval_cli.py::eval_app`                                       | `app.add_typer(eval_app, name="eval")`                            | WIRED       | `cli.py:519,521` deferred-import block at bottom.                                                       |
| `eval_cli.py`                          | `evaluation.py::load_evaluation_dataset`                       | dataset load with `EvaluationDatasetError` exit-1                 | WIRED       | `eval_cli.py:70,127,203`.                                                                              |
| `eval_cli.py`                          | `models.py::IndexMissingError`                                | catch and surface German message + exit 1                          | WIRED       | `eval_cli.py:71,144–151`.                                                                              |

### Data-Flow Trace (Level 4)

These artifacts produce CLI output and JSON payloads — verifying upstream data sources:

| Artifact                        | Data Variable                       | Source                                                                                                  | Produces Real Data | Status     |
| ------------------------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------ | ---------- |
| `_emit_human_report` (eval_cli) | `result: EvalRunResult`             | `EvalRunner(settings).run(evaluation_dataset, ...)` at `eval_cli.py:138` — real runner, no mock fallback. | Yes                | FLOWING    |
| `dump_json_report` (eval_cli)    | `result: EvalRunResult`             | Same `EvalRunner.run` output.                                                                            | Yes                | FLOWING    |
| `build_json_report` (eval_report) | `result.cases`, `result.meta`, `result.summary` | Real dataclass attributes from `EvalRunner.run`; tuples → lists; dict pass-through.                | Yes                | FLOWING    |
| `EvalRunner._run_case`           | `query_result: QueryResult`         | `engine.query(case.query)` — real `RagEngine` constructed with effective settings.                       | Yes                | FLOWING    |
| `summarize_retrieval_metrics`    | `retrieval_metrics` list             | Built by `evaluate_retrieval_case(case, query_result.sources)` per non-skipped/errored case.             | Yes                | FLOWING    |

### Behavioral Spot-Checks

| Behavior                                                                   | Command                                                                       | Result                                                                  | Status |
| -------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ----------------------------------------------------------------------- | ------ |
| Forward import safety: `from ood.cli import app` works                      | `uv run python -c "from ood.cli import app; print('forward_ok')"`             | `forward_ok`                                                            | PASS   |
| Reverse import safety: `from ood.eval_cli import eval_app` works            | `uv run python -c "from ood.eval_cli import eval_app; print('reverse_ok')"`   | `reverse_ok`                                                            | PASS   |
| `ood eval --help` lists both subcommands                                   | `uv run ood eval --help`                                                       | Shows `run` and `cases` with German help strings; exit 0.               | PASS   |
| `ood eval run --help` exposes documented flags                              | `uv run ood eval run --help`                                                   | Lists `--dataset`, `--case-id`, `--out`, `--json`, `--verbose`, `--quiet`, `--knowledge-dir`, `--data-dir`, `--storage-dir`. | PASS |
| `OOD_EVAL_DATASET` env var binds to `Settings.eval_dataset_path`            | `OOD_EVAL_DATASET=/tmp/foo_test.json uv run python -c "from ood.config import Settings; print(Settings().eval_dataset_path)"` | `/tmp/foo_test.json`                                                    | PASS   |
| Eval test suite runs green                                                 | `uv run pytest tests/test_eval_runner.py tests/test_eval_report.py tests/test_eval_cli.py -q` | `55 passed in 0.53s`                                                    | PASS   |
| Full project suite runs green (no regressions)                              | `uv run pytest tests/ -q`                                                      | `181 passed in 1.03s`                                                   | PASS   |
| Eval runner has 0 references to `can_use_cloud_llm`                         | `grep -c "can_use_cloud_llm" src/ood/eval_runner.py`                           | `0`                                                                     | PASS   |
| Eval runner has 3 references to `allow_cloud_llm` (all inside `_engine_settings` block) | `grep -c "allow_cloud_llm" src/ood/eval_runner.py`                | `3` — guarded by `test_run_does_not_consult_allow_cloud_llm_in_business_logic` source-inspection test. | PASS   |

### Requirements Coverage

| Requirement | Source Plan        | Description                                                                                                                | Status     | Evidence                                                                                                                       |
| ----------- | ------------------ | -------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------ |
| EVAL-02     | 13-01, 13-03       | User can run evaluations through the public `RagEngine.query()` contract so retrieval backends stay black-box interchangeable. | SATISFIED  | `eval_runner.py:224` single dispatch point via `engine.query(case.query)`. CLI invokes `EvalRunner.run`. 17 runner tests cover the contract. |
| EVAL-06     | 13-02, 13-03       | User can consume evaluation results in both concise human-readable CLI output and structured JSON output.                  | SATISFIED  | `_emit_human_report` (German human format), `dump_json_report` (wire schema `schema_version=1`). 14 report + 24 CLI tests passing. |
| EVAL-07     | 13-01, 13-02, 13-03 | User can run evaluation locally without Cloud LLM usage by default, with every report explicitly showing `llm_used`.        | SATISFIED  | Default `llm_used=False`; runner gate `has_llm_credentials` only; `»LLM«` marker prefix; D-07 three-level propagation enforced by `test_build_json_report_propagates_llm_used_at_three_levels`. |

REQUIREMENTS.md confirms all three IDs are Phase-13-mapped and marked Complete (lines 98, 102, 103). No orphaned requirements: REQUIREMENTS.md does not map any other IDs to Phase 13 that are missing from the plans.

### Anti-Patterns Found

None. No TODO/FIXME/placeholder/XXX/HACK comments in any of the three production files. Empty `return ()` constructions occur only as legitimate defaults for `command_args` tuple, and `_engine_settings` returns the unchanged Settings object when credentials are absent — not a stub, this is the documented passthrough path.

### Human Verification Required

None. All goal-relevant behaviors are observable in code or via CLI/test commands and have been verified. The end-to-end smoke against a real-on-disk index is documented in 13-03-SUMMARY.md as requiring an external setup step (mock corpus generation), but the same code path is covered by `test_eval_run_exit_code_one_when_index_missing` (BLOCKER 2 follow-through) via runner→CLI chain with a monkeypatched `RagEngine.query` raising `IndexMissingError`.

### Gaps Summary

None. All nine derived truths are verified, all artifacts exist and are substantive and wired, all three EVAL requirements are satisfied, all 55 phase-specific tests and 181 total tests pass, and both import directions work without a circular `ImportError`. The phase goal — "User can run local black-box evaluations through `RagEngine.query()` and consume reports in both human-readable and machine-readable forms" — is achieved end-to-end.

---

*Verified: 2026-05-11T11:00:00Z*
*Verifier: Claude (gsd-verifier)*
