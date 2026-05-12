---
phase: 13-evaluation-service-and-cli-reporting
plan: 03
subsystem: evaluation
tags: [evaluation, cli, typer, german-ui, llm-marker, exit-code-policy, import-safety]
requires:
  - phase: 13-evaluation-service-and-cli-reporting
    provides: EvalRunner, EvalRunResult, EvalRunnerError, SCHEMA_VERSION (Plan 01)
  - phase: 13-evaluation-service-and-cli-reporting
    provides: build_json_report, dump_json_report (Plan 02)
provides:
  - eval_app Typer sub-app registered under `ood eval` with `run` and `cases` subcommands
  - German human formatter with `»LLM«` marker (D-07), summary block, and failure/skipped/errored sections (D-03/D-08/D-10)
  - Single JSON wire-schema emission via Plan 02 serializer for both --json (stdout, compact) and --out (file, indent=2)
  - Exit-code policy: 0 on successful run regardless of pass/fail counts; 1 on hard errors (D-09)
  - IndexMissingError → German message "Kein Index gefunden. Bitte zuerst `ood index` ausführen." (D-04 / D-09)
  - Forward AND reverse-direction import safety contract (WARNING 4): `from ood.cli import app` and `from ood.eval_cli import eval_app` both succeed
affects: [phase-14-baseline-feedback-loop-and-review-gate, evaluation-reporting, skill-integration]
tech-stack:
  added: []
  patterns:
    - "Deferred bottom-of-module registration: `cli.py` imports `eval_app` only at the very bottom, after all helpers/option types are defined, so eval_cli can import from cli during normal loading."
    - "Reverse-direction safe partial load: `eval_app = typer.Typer(...)` is defined BEFORE the `from ood.cli import (...)` statement so a reverse-first import (`from ood.eval_cli import eval_app`) survives the partial-load re-entry that cli.py's deferred import triggers."
    - "German user-facing strings + English JSON keys split (D-04): the formatter maps Hit@1/mrr/intent_accuracy to German display labels at the rendering boundary only; the JSON builder is data-only."
    - "Exit-code as posture signal: failed/errored cases never abort the run; only hard errors (dataset / runner config / index missing) map to exit 1."
key-files:
  created:
    - src/ood/eval_cli.py
    - tests/test_eval_cli.py
  modified:
    - src/ood/cli.py
key-decisions:
  - "Define `eval_app` BEFORE the `from ood.cli import (...)` line in `eval_cli.py` so the reverse-direction circular import (cli.py re-entering eval_cli during its own bottom-of-file deferred import) finds the symbol in the partial-load namespace. The plan's original assumption — that eval_app would be reached during decorator execution — was wrong; the re-entry actually happens DURING the `from ood.cli import (...)` statement, before any decorators run."
  - "Use `--knowledge-dir` in test fixtures with a tmp knowledge directory containing stub Markdown files for every `expected_sources` path, because `load_evaluation_dataset` (used unchanged from Plan 01) validates expected source paths against `settings.knowledge_dir`. The plan's listed test inputs assumed validation would silently pass; the actual contract is stricter."
  - "Human formatter uses 4-decimal float formatting for all aggregate metrics (`f\"{value:.4f}\"`), mirrors English JSON metric keys to German display labels (`Hit@1`/`MRR`/`Source-Recall`/etc.), and renders Mismatch lines for failed cases by enumerating every False boolean and every sub-1.0 ratio in retrieval_metrics + ticket_metrics."
  - "`ood eval cases` validates source paths via `load_evaluation_dataset(..., knowledge_dir=settings.knowledge_dir)` — same contract as `run`. Users listing cases on a fresh dataset must point `--knowledge-dir` at a location that contains the referenced Markdown files."
patterns-established:
  - "Reverse-direction circular-import safety: in any module pair (A → B with B importing helpers from A at module-load and A registering a B-defined Typer sub-app at the bottom), the B-side public symbol (here `eval_app`) MUST be defined BEFORE B's `from A import (...)` statement to survive partial-load re-entry."
  - "CLI-side translation of internal English error messages: `IndexMissingError(\"No index found. Run `ood index` first.\")` is caught at the CLI boundary and rewritten to the German user-facing string `\"Kein Index gefunden. Bitte zuerst `ood index` ausführen.\"`. The underlying exception keeps its English message for logs/Python tracebacks."
requirements-completed: [EVAL-02, EVAL-06, EVAL-07]
duration: 8min
completed: 2026-05-11
---

# Phase 13 Plan 03: ood eval CLI Summary

**`ood eval run` / `ood eval cases` wire the EvalRunner (Plan 01) and JSON serializer (Plan 02) behind a German Typer sub-app, render the locked human format with the `»LLM«` marker, and enforce the D-09 exit-code policy — including the now-reachable IndexMissingError exit-1 path.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-05-11T08:14:15Z
- **Completed:** 2026-05-11T08:22:10Z
- **Tasks:** 1 (TDD, red+green)
- **Files created:** 2 (`src/ood/eval_cli.py`, `tests/test_eval_cli.py`)
- **Files modified:** 1 (`src/ood/cli.py` — deferred-import registration)
- **Tests added:** 24
- **Full project suite after Plan 03:** **181 passed** (up from 157 after Plan 02)

## Accomplishments

- `eval_app = typer.Typer(name="eval", help="Lokale Evaluation des OOD Agents über RagEngine.query().", no_args_is_help=True)` is registered under the top-level `app` via `app.add_typer(eval_app, name="eval")` at line 521 of `src/ood/cli.py` (deferred import at the very bottom of the file).
- `ood eval --help` shows both subcommands (`run`, `cases`) and the German help string.
- `ood eval run` flag set: `--dataset`, `--case-id`, `--out`, `--json`, `--verbose/-v`, `--quiet/-q`, `--knowledge-dir`, `--data-dir`, `--storage-dir` (last three reuse the option types from `ood.cli` for parity with `ood query`).
- Dataset resolution: `(dataset or settings.eval_dataset_path).resolve()`. `OOD_EVAL_DATASET` env-var is honored via `Settings.eval_dataset_path` (Plan 01 contract). `--dataset` flag overrides it.
- `load_evaluation_dataset(dataset_path, knowledge_dir=settings.knowledge_dir)` is called BEFORE constructing the runner. `FileNotFoundError` → `Datensatz nicht gefunden: {dataset_path}` (stderr, exit 1). `EvaluationDatasetError` → `Datensatz konnte nicht geladen werden: {error}` (stderr, exit 1).
- `EvalRunner(settings).run(...)` is the single dispatch point. `command_args=tuple(sys.argv[1:])` records the CLI invocation in `EvalRunMeta.command_args`.
- `IndexMissingError` raised by `EvalRunner.run()` (per Plan 13-01 BLOCKER 2 fix) is caught at the CLI boundary and rewritten to the German message `"Kein Index gefunden. Bitte zuerst \`ood index\` ausführen."` — exit code 1 (D-09).
- `EvalRunnerError` (e.g. unknown `--case-id`) → stderr passes through, exit 1.
- `--json` emits `dump_json_report(result, indent=None)` (compact) to stdout. `--out` writes `dump_json_report(result, indent=2)` to the path; parent directories are created automatically. Both flags may be combined.
- Without `--json` and without `--quiet`, `_emit_human_report(result)` renders the German human format. With `--quiet`, no stdout (file output still written if `--out` is given).
- `ood eval cases` lists `case_id: query-first-line` lines sorted by `case_id`, or `{"dataset": ..., "cases": [{"case_id", "query"}, ...]}` JSON with `--json`. No runner instantiation, no engine boot.
- **D-07 marker:** when `meta.llm_used` is True, line 2 of the human report becomes `»LLM« Cloud-LLM verwendet: ja`. Otherwise: `Cloud-LLM verwendet: nein`.
- **D-03 enumeration policy:** passed cases never appear by name in the human output — only counted in the Summary block. Failed cases render expected/actual sources + Mismatch line (every False boolean and every sub-1.0 ratio in retrieval_metrics/ticket_metrics).
- **D-08/D-10 isolation:** skipped and errored cases get their own sections (`Übersprungene Fälle`, `Fehler:`) and do not appear under `Fehlgeschlagene Fälle`.

## Sample German Human Output (1 passed, 1 failed, 1 skipped)

```
OOD Evaluation — Datum: 2026-05-10T16:39:04Z — Retrieval-Backend: local_vector_graph_index
Cloud-LLM verwendet: nein
Datensatz: mock-v1 (evaluation/datasets/mock-v1.json)

Zusammenfassung:
  Fälle gesamt:        3
  Bestanden:           1
  Fehlgeschlagen:      1
  Übersprungen:        1   (Grund: llm_required)
  Fehler:              0
  Aggregiert:          2   (ohne Übersprungen/Fehler)

Retrieval-Metriken (aggregiert):
  Hit@1:               1.0000
  Hit@3:               1.0000
  Hit@5:               1.0000
  MRR:                 1.0000
  Source-Recall:       1.0000
  Forbidden-Source:    0.0000

Ticket-Intelligenz (aggregiert):
  Intent-Accuracy:     1.0000
  Routing-Accuracy:    1.0000
  Identifier-Recall:   1.0000
  Command-Risk:        1.0000
  Uncertainty:         1.0000

Fehlgeschlagene Fälle:
  - case-fail-0 — "Police MOCK-POL-1003 …"
      Erwartet:  ticket/mock-pol-1003.md, wiki/mock-wiki-5003.md
      Aktuell:   wiki/mock-wiki-5003.md (0.71), note/mock-note-7003.md (0.55)
      Mismatch:  Hit@1=False, mrr=0.50, source_recall=0.50, intent_match=False

Übersprungene Fälle:
  - case-skip-0 — Grund: llm_required (erwartete LLM-Antwort liegt vor; keine LLM-Credentials konfiguriert)

Fehler:
  (keine)
```

When `meta.llm_used=True`, line 2 changes to: `»LLM« Cloud-LLM verwendet: ja`.

## Public Surface (consumed by Phase 14)

```python
# src/ood/eval_cli.py
eval_app: typer.Typer  # registered as `ood eval`

@eval_app.command("run")
def run(
    dataset: Path | None = None,
    case_id: str | None = None,
    out: Path | None = None,
    json_output: bool = False,
    verbose: bool = False,
    quiet: bool = False,
    knowledge_dir: Path | None = None,
    data_dir: Path | None = None,
    storage_dir: Path | None = None,
) -> None: ...

@eval_app.command("cases")
def cases(
    dataset: Path | None = None,
    json_output: bool = False,
    quiet: bool = False,
    knowledge_dir: Path | None = None,
    data_dir: Path | None = None,
) -> None: ...
```

`__all__ = ["eval_app"]`. The CLI bottom-of-`cli.py` deferred import is the only public registration point — third-party callers should import `eval_app` from `ood.eval_cli` directly when they need to embed it.

## Task Commits

1. **Task 1 (TDD): Build eval Typer sub-app with run/cases, German formatter, exit-code policy, IndexMissingError mapping, and reverse-direction import safety** — `6197264` (test/RED), `2d1f7de` (feat/GREEN)

Both commits include the test/implementation pair for the same atomic deliverable. No separate refactor commit was needed.

## German `IndexMissingError` Message

- **Exact text:** `Kein Index gefunden. Bitte zuerst \`ood index\` ausführen.`
- **Location:** `src/ood/eval_cli.py` line 149
- **Stream:** stderr (via `typer.echo(..., err=True)`)
- **Exit code:** 1

The underlying `IndexMissingError` keeps its English message (`"No index found. Run \`ood index\` first."`) for Python tracebacks and logs; the CLI rewrites it at the boundary to keep all user-visible strings in German (D-04).

## Test Catalogue (24 tests)

| #   | Test                                                          | Covers                                                    |
| --- | ------------------------------------------------------------- | --------------------------------------------------------- |
| 1   | `test_eval_help_shows_run_and_cases`                          | help text exposes both subcommands                        |
| 2   | `test_eval_run_help_lists_documented_flags`                   | --dataset, --case-id, --out, --json in run --help         |
| 3   | `test_eval_run_uses_settings_eval_dataset_path_by_default`    | OOD_EVAL_DATASET env-var default                          |
| 4   | `test_eval_run_dataset_flag_overrides_env`                    | --dataset overrides env                                   |
| 5   | `test_eval_run_missing_dataset_exits_1`                       | FileNotFoundError → German + exit 1                       |
| 6   | `test_eval_run_malformed_dataset_exits_1`                     | EvaluationDatasetError → German + exit 1                  |
| 7   | `test_eval_run_renders_german_header_with_llm_used_no`        | header line 1, line 2, summary keywords                   |
| 8   | `test_eval_run_renders_llm_marker_when_llm_used_true`         | D-07 »LLM« marker prefix                                  |
| 9   | `test_eval_run_human_output_does_not_enumerate_passed_cases`  | D-03 — pass cases never enumerated                        |
| 10  | `test_eval_run_human_output_lists_failed_cases_with_...`      | failed case rendering + Mismatch line                     |
| 11  | `test_eval_run_human_output_lists_skipped_cases_separately`   | D-08 isolation                                            |
| 12  | `test_eval_run_human_output_lists_errored_cases_separately`   | D-10 isolation                                            |
| 13  | `test_eval_run_exit_code_zero_when_failures_present`          | D-09: exit 0 with failed cases                            |
| 14  | `test_eval_run_exit_code_zero_when_errored_present`           | D-09 + D-10: exit 0 with errored cases                    |
| 15  | `test_eval_run_json_emits_wire_schema_to_stdout`              | schema_version, llm_used, summary, cases in JSON          |
| 16  | `test_eval_run_out_writes_indented_json_to_file`              | --out file (indent=2) + --json stdout combinable          |
| 17  | `test_eval_run_out_creates_parent_directories`                | --out creates missing parent dirs                         |
| 18  | `test_eval_run_unknown_case_id_exits_1`                       | EvalRunnerError → exit 1                                  |
| 19  | `test_eval_run_index_missing_exits_1`                         | IndexMissingError raised from run() → German + exit 1     |
| 20  | `test_eval_run_exit_code_one_when_index_missing`              | BLOCKER 2 e2e: RagEngine.query → IndexMissingError → exit 1 |
| 21  | `test_eval_cases_lists_sorted_case_ids_with_query`            | sorted listing                                            |
| 22  | `test_eval_cases_json_emits_dataset_name_and_cases`           | JSON shape: dataset + cases array                         |
| 23  | `test_eval_cli_quiet_suppresses_human_output`                 | --quiet suppresses stdout                                 |
| 24  | `test_eval_cli_module_importable_directly`                    | WARNING 4 reverse-direction import safety (subprocess)    |

## Import Safety Contract

`src/ood/eval_cli.py` is structured so that **both** import directions succeed regardless of which module loads first:

```python
# Top of src/ood/eval_cli.py
import typer
# ... stdlib imports ...

# >>> eval_app DEFINED HERE <<<
eval_app = typer.Typer(name="eval", ...)

# Only AFTER eval_app exists do we import from ood.cli (which will
# re-enter this module via its own bottom-of-file deferred import).
from ood.cli import (
    DataDirOption, JsonOption, ..., _handle_error, _load_valid_settings,
)
# ...
```

```python
# Bottom of src/ood/cli.py (line 519-521)
from ood.eval_cli import eval_app  # noqa: E402  (deferred to avoid circular import)
app.add_typer(eval_app, name="eval")
```

**Forward direction:** `from ood.cli import app` → loads cli.py top to bottom → at the bottom imports `eval_app` → loads eval_cli.py → eval_cli imports from cli (already fully loaded, all helpers present) → succeeds.

**Reverse direction:** `from ood.eval_cli import eval_app` → starts loading eval_cli.py → defines `eval_app` → imports from cli → loads cli.py → at the bottom of cli.py does `from ood.eval_cli import eval_app` → re-enters eval_cli, which is partially loaded but `eval_app` is already bound → succeeds.

Test `test_eval_cli_module_importable_directly` runs a fresh subprocess to verify this — guards against future refactors that could re-introduce the partial-load circular `ImportError`.

## OOD_EVAL_DATASET Contract

`OOD_EVAL_DATASET=/path/to/dataset.json` is the default-source contract for the dataset path (bound to `Settings.eval_dataset_path` via `AliasChoices` per Plan 01). `--dataset <path>` overrides it. When neither is set, `Settings.eval_dataset_path` falls back to `Path("evaluation/datasets/mock-v1.json")`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Plan's stated reverse-direction import safety approach was insufficient**

- **Found during:** Task 1 GREEN step (first test run after creating eval_cli.py).
- **Issue:** The plan's behavior section (lines 244-245) claimed that defining `eval_app` "near the top of `eval_cli.py` BEFORE any of the @eval_app.command bodies execute" would satisfy the reverse-direction re-entry. In practice, the re-entry triggered by `cli.py`'s bottom-of-file deferred import happens WHILE eval_cli.py is paused on its own `from ood.cli import (...)` statement — BEFORE the decorators run AND before the module body following the import block executes. With the plan's original layout (`from ood.cli import (...)` near the top, then `eval_app = ...` after), the re-entry crashes with `ImportError: cannot import name 'eval_app' from partially initialized module 'ood.eval_cli'`.
- **Fix:** Move `eval_app = typer.Typer(...)` to be the very first non-import statement in `eval_cli.py`, BEFORE the `from ood.cli import (...)` line. This way the re-entry finds `eval_app` already bound in the partial-load namespace. Added a long comment block above the `eval_app` definition documenting the constraint for future maintainers.
- **Files modified:** `src/ood/eval_cli.py`
- **Commit:** `2d1f7de` (GREEN — the fix is part of the initial implementation since RED couldn't even collect)

**2. [Rule 3 — Blocking] `CliRunner(mix_stderr=False)` not supported in installed typer version**

- **Found during:** Task 1 first GREEN run.
- **Issue:** Tests instantiated `CliRunner(mix_stderr=False)` (a Click 7-era idiom referenced in the plan). The installed typer wraps Click 8+, which removed the `mix_stderr` constructor argument; `result.stderr` is already a separate attribute by default.
- **Fix:** Use `CliRunner()` (no arguments). Tests that assert on stderr content fall back to checking the combined `stderr + stdout` in case the runner merges streams. All 24 tests pass either way.
- **Files modified:** `tests/test_eval_cli.py`
- **Commit:** `2d1f7de` (folded into GREEN — the failing test_eval_cli.py never had a passing state before this fix)

**3. [Rule 3 — Blocking] Test fixtures must include a knowledge-dir with stub Markdown for every expected_sources path**

- **Found during:** Task 1 GREEN step.
- **Issue:** The plan-listed test text (lines 446-484) wrote single-case datasets and invoked the CLI without `--knowledge-dir`. Because the CLI passes `knowledge_dir=settings.knowledge_dir` to `load_evaluation_dataset` (which validates that every expected source path EXISTS under the knowledge dir per Phase 12 Plan 01), the dataset load fails with `EvaluationDatasetError: Evaluation dataset references missing knowledge source paths: ticket/mock-pol-1001.md`.
- **Fix:** Added `_make_knowledge_dir(tmp_path)` helper that creates a tmp knowledge dir with stub Markdown files for every path used in dataset fixtures. Tests pass `--knowledge-dir str(knowledge_dir)` alongside `--dataset`. This is a fixture-only change; the CLI behavior is unchanged.
- **Files modified:** `tests/test_eval_cli.py`
- **Commit:** `2d1f7de` (folded into GREEN)

No CLAUDE.md violations, no project-instruction divergence — work was performed entirely through the `/gsd:execute-phase` flow.

### Architectural Changes

None.

## Auth Gates

None. The eval CLI is a pure local-orchestration surface — no external service calls, no credentials, no auth steps.

## Known Stubs

None. `eval_app.run` calls real `EvalRunner.run` and renders the real `EvalRunResult`; `eval_app.cases` calls real `load_evaluation_dataset`. The fake-runner monkeypatch lives only in tests.

## Deferred Issues

None within scope of this plan.

**Out-of-scope discoveries (not fixed, not blocking):**

- `ood eval cases` against a real-on-disk dataset (`evaluation/datasets/mock-v1.json`) currently requires `--knowledge-dir` pointing to a directory that contains every referenced source Markdown file, because `load_evaluation_dataset` validates source paths. For UX, a future plan could add a `--no-validate-sources` flag to `cases` so users can list cases without provisioning the knowledge dir. Tracked as a UX nit, not a bug.

## Issues Encountered

- The plan's import-safety analysis (reverse-direction re-entry) was wrong about WHEN the re-entry happens. Fixed by relocating `eval_app = typer.Typer(...)` above the `from ood.cli import (...)` block. See Deviation #1.
- `CliRunner(mix_stderr=False)` is not supported in the installed typer/Click version. See Deviation #2.
- `load_evaluation_dataset` validation against `knowledge_dir` requires test fixtures to create stub Markdown files. See Deviation #3.

All issues resolved automatically per Rule 1 / Rule 3 — no architectural change needed.

## User Setup Required

None for the CLI itself. To run an end-to-end smoke against the committed `evaluation/datasets/mock-v1.json`, the user must first either:

1. Generate the mock corpus via `ood mock-init --target-dir knowledge/mock/v1` (creates stub Markdown files), then run `ood eval run --knowledge-dir knowledge/mock/v1`, OR
2. Run against a different dataset whose `expected_sources` paths exist under the configured knowledge dir.

This is a pre-existing Phase 12 behavior (source-path validation in `load_evaluation_dataset`) — not introduced by this plan.

## Verification

- `uv run pytest tests/test_eval_cli.py -x` → **24 passed**
- `uv run pytest tests/test_eval_runner.py tests/test_eval_report.py tests/test_eval_cli.py -x` → **55 passed**
- `uv run pytest -q` → **181 passed** (full project suite, up from 157 after Plan 02)
- `grep -q "eval_app = typer.Typer" src/ood/eval_cli.py` → ok
- `grep -q "@eval_app.command(\"run\")" src/ood/eval_cli.py` → ok
- `grep -q "@eval_app.command(\"cases\")" src/ood/eval_cli.py` → ok
- `grep -q "add_typer(eval_app" src/ood/cli.py` → ok (line 521)
- `grep -q "Cloud-LLM verwendet:" src/ood/eval_cli.py` → ok
- `grep -q "»LLM«" src/ood/eval_cli.py` → ok
- `grep -q "Fehlgeschlagene Fälle" src/ood/eval_cli.py` → ok
- `grep -q "Übersprungene Fälle" src/ood/eval_cli.py` → ok
- `grep -q "except IndexMissingError" src/ood/eval_cli.py` → ok
- `grep -q "Kein Index gefunden" src/ood/eval_cli.py` → ok (line 149)
- `grep -q "build_json_report\|dump_json_report" src/ood/eval_cli.py` → ok (uses Plan 02 serializer directly)
- `uv run python -c "from ood.cli import app; print('ok')"` → `ok` (forward direction)
- `uv run python -c "from ood.eval_cli import eval_app; print('ok')"` → `ok` (reverse direction — WARNING 4 covered)
- `uv run ood eval --help` exits 0, lists `run` and `cases`.
- `uv run ood eval run --help` exits 0, lists `--dataset`, `--case-id`, `--out`, `--json`, `--verbose`, `--quiet`, `--knowledge-dir`, `--data-dir`, `--storage-dir`.
- Targeted `-k` runs (D-09, D-07, D-03, JSON, IndexMissingError, BLOCKER 2 e2e, WARNING 4) → **7 passed**.

## Next Plan Readiness

**Phase 14 (Baseline, Feedback Loop, and Review Gate)** can now:

- Drive `ood eval run --json` from Python/CI to produce reproducible wire-schema reports (`schema_version=1`).
- Use `ood eval run --out <baseline.json>` to seed a v1.1 baseline file.
- Parse the JSON output directly via `json.loads` — German strings round-trip verbatim (Plan 02's `ensure_ascii=False`).
- Use `meta.llm_used` (or the `»LLM«` marker in human output) as the privacy-posture signal at the top of every report.
- Rely on D-09: failed/errored cases never propagate as exit 1, so CI can distinguish "evaluation produced a report" (exit 0) from "evaluation could not run" (exit 1).
- Use `ood eval cases` to enumerate the case set for stratified sampling / review-gate workflows.

## Self-Check: PASSED

Files exist:

- `src/ood/eval_cli.py` → FOUND
- `tests/test_eval_cli.py` → FOUND
- `src/ood/cli.py` (with `add_typer(eval_app)`) → FOUND
- `.planning/phases/13-evaluation-service-and-cli-reporting/13-03-SUMMARY.md` → FOUND (this file)

Commits exist in `git log --oneline -6`:

- `6197264` (test/RED Task 1) → FOUND
- `2d1f7de` (feat/GREEN Task 1) → FOUND

---
*Phase: 13-evaluation-service-and-cli-reporting*
*Completed: 2026-05-11*
