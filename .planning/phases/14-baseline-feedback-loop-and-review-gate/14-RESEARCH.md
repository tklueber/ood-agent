# Phase 14: Baseline, Feedback Loop, and Review Gate - Research

**Researched:** 2026-05-11  
**Domain:** Local evaluation baseline snapshots, failed-case review artifacts, and explicit approval gate CLI workflow  
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

## Implementation Decisions

### Baseline Artifact

- **D-01:** Create an explicit baseline snapshot flow rather than relying only on ad-hoc `ood eval run --out` files. The baseline is a deliberate user action and must not be auto-promoted from every eval run.
- **D-02:** The first baseline is observational: it records current metrics, metadata, and case outcomes, but it does not introduce arbitrary hard thresholds or convert ordinary failed cases into process-level exit failures.

### Review Records

- **D-03:** Failed-case review artifacts must include evidence and decision data: expected sources, actual sources, mismatch metrics, proposed next action, reviewer decision, rationale/notes, owner or reviewer identity where available, date/time, and baseline-update status.
- **D-04:** Review artifacts should distinguish at least approved, rejected, and deferred outcomes so downstream workflows can avoid treating every metric change as accepted improvement.

### Command Flow

- **D-05:** Extend the existing `ood eval` namespace for Phase 14 commands instead of adding unrelated top-level commands. Phase 13 deliberately chose this namespace to allow later commands such as baseline/review/update without naming churn.
- **D-06:** Exact command names, flags, and file paths are planner discretion, but they must preserve the existing CLI style: Typer commands, German human-facing strings, English JSON keys, `--dataset`/path override conventions, and stdout/file output separation.

### Acceptance Gate

- **D-07:** Baseline updates and accepted improvement status require an explicit approved review decision. Rejected or deferred review records must not update the baseline.
- **D-08:** Metric improvement alone is not enough to accept a change in this phase. The review gate exists to prevent premature automated thresholds and to ensure corpus/retrieval changes are consciously accepted.

### the agent's Discretion

- Planner decides the exact baseline and review file locations, but recommended defaults should live under ignored runtime/report directories when generated automatically and avoid committing volatile run artifacts by default.
- Planner decides whether baseline and review artifacts are pure JSON, Markdown plus JSON, or JSON with a human summary, as long as failed-case evidence and explicit decisions are machine-readable.
- Planner decides the minimal number of commands needed. Prefer a small cohesive CLI surface over a broad command set.

### Deferred Ideas (OUT OF SCOPE)

## Deferred Ideas

- Hard CI regression gates with calibrated thresholds remain deferred to future EVAL-10 work.
- Historical trend comparison remains deferred until baseline mechanics and review decisions exist.
- LLM-as-judge answer scoring remains deferred and requires explicit privacy approval.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EVAL-05 | User can establish a first baseline report without arbitrary hard thresholds before representative mock data exists | Use explicit observational baseline snapshot command, store existing `schema_version=1` report plus baseline metadata, keep eval exit behavior unchanged, and avoid pass/fail process gates. |
| EVAL-11 | User can use a feedback loop with a review gate that records failed cases, proposed corpus/query fixes, reviewer decision, and baseline update status | Add failed-case review artifact generation, explicit `approved/rejected/deferred` decision records, and gate baseline updates on approved decisions only. |
</phase_requirements>

## Summary

Phase 14 should be implemented as a thin, local workflow layer on top of the Phase 13 evaluation runner and JSON report serializer. The correct planning unit is not a new evaluator or metric engine; it is a set of deliberate CLI actions under `ood eval` that persist an observational baseline, generate failed-case review artifacts from existing report evidence, and require explicit human approval before treating corpus/retrieval/baseline changes as accepted improvements.

The existing Phase 13 contracts are strong enough to support this without new third-party dependencies: `EvalRunner.run(...)` produces `EvalRunResult`, `dump_json_report(...)` emits the locked `schema_version=1` JSON report, `ood eval run --out` already creates parent directories, and failed cases already include expected sources, actual sources, retrieval metrics, ticket metrics, query result evidence, `llm_used`, dataset hash/path, and command args. Phase 14 should reuse those contracts and add small OOD-owned dataclasses/helpers for baseline metadata, review records, and gate decisions.

**Primary recommendation:** Add minimal `ood eval baseline`, `ood eval review`, and `ood eval approve`/`update-baseline` style commands that read/write machine-readable JSON artifacts under ignored `data/` defaults, never auto-promote eval runs, and only update the baseline when a review record contains an explicit approved decision.

## Project Constraints (from AGENTS.md)

- No `AGENTS.md` exists in the repository root — verified by glob.
- No project-local `.claude/skills/` or `.agents/skills/` directories exist — verified by glob.
- CLAUDE/project instructions still apply:
  - Python, LightRAG, Cloud-LLM only after privacy approval; Markdown remains canonical knowledge format.
  - Ticket contents may only be sent to Cloud LLM when privacy approval exists; Phase 13 eval deliberately records `llm_used` and forges eval LLM behavior on credentials, so Phase 14 artifacts must preserve/report this privacy posture.
  - Secrets only via `.env` or environment variables; never in Markdown sources, generated docs, reports intended for commit, or git history.
  - MVP remains local; generated runtime reports and indexes belong under ignored `data/` by default.
  - Human CLI strings are German; JSON keys stay English.
  - Existing GSD workflow says no direct repo edits outside workflow; this research writes only the required planning artifact.

## Standard Stack

### Core

| Library / Module | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `json` + `pathlib` | Python runtime via `uv`; project supports `>=3.10` | Read/write baseline and review artifacts as UTF-8 JSON, create parent directories, validate fields | Already used in `eval_report.py`; Python docs confirm `json.dumps(..., ensure_ascii=False, indent=...)` and `json.loads` are standard for JSON serialization/deserialization. |
| Typer | 0.25.1 installed | Add subcommands under existing `ood eval` namespace | Existing CLI uses Typer; official docs support command groups/subcommands and options. Phase 13 import-safety pattern is already established. |
| OOD `EvalRunner` | internal | Produce typed evaluation run results through `RagEngine.query()` | Existing source of truth for per-case outcomes and summary metrics. Do not duplicate eval logic. |
| OOD `eval_report.dump_json_report` / `build_json_report` | internal `schema_version=1` | Serialize baseline source report | Phase 13 explicitly made this the single JSON wire-schema serializer. Use it for baseline snapshots. |

### Supporting

| Library / Module | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 9.0.3 installed | Unit/CLI tests for baseline/review/gate behavior | Follow existing `tests/test_eval_cli.py`, `tests/test_eval_runner.py`, `tests/test_eval_report.py` patterns; use `tmp_path` for generated artifacts. |
| dataclasses | stdlib | Immutable OOD-owned models for baseline/review records | Use for internal typed contracts, mirroring `EvalCaseResult`/`EvalRunResult`. |
| hashlib | stdlib | Hash report/review artifacts for provenance | Already used by `EvalRunner` for dataset hash; useful for baseline report hash and gate validation. |
| datetime | stdlib | UTC timestamps for baseline/review decisions | Follow Phase 13 ISO-8601 UTC `...Z` style. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| JSON-only artifacts | Markdown summary plus adjacent JSON | Markdown is easier for humans but risks schema drift. If used, JSON must remain canonical and machine-readable. |
| Dedicated top-level commands | `ood baseline`, `ood review` | Contradicts locked D-05 and loses namespace continuity. Do not use. |
| CI threshold gates | Non-zero exit on failed cases / fixed thresholds | Explicitly deferred. Current phase is observational + reviewed approval, not automated regression enforcement. |
| External eval/reporting tools | Evidently/MLflow/custom dashboard | Overkill and contrary to local CLI-first milestone; current data is JSON reports and mock corpus. |

**Installation:** No new runtime dependencies recommended.

```bash
# no dependency additions required
uv sync
```

**Version verification:** Installed package versions were checked with `uv run python -c "import importlib.metadata ..."`: Typer 0.25.1, Pydantic 2.13.3, pydantic-settings 2.14.0, pytest 9.0.3, Ruff 0.15.12, mypy 1.20.2. `uv --version` reports 0.9.7. Python system `python3` is 3.9.6, but project commands should run through `uv` because `requires-python = ">=3.10"`.

## Architecture Patterns

### Recommended Project Structure

```text
src/ood/
├── eval_cli.py          # Extend existing eval_app; keep import-safety ordering
├── eval_report.py       # Reuse only; do not fork schema_version=1 serializer
├── eval_runner.py       # Reuse only; do not recompute metrics here
├── eval_baseline.py     # Recommended new pure artifact service/dataclasses
└── evaluation.py        # Reuse dataset loader/path validation

tests/
├── test_eval_cli.py          # CLI coverage can be extended if small
├── test_eval_baseline.py     # Recommended focused unit tests for artifact logic
└── test_eval_report.py       # Existing schema tests; do not destabilize

data/                       # ignored; recommended default runtime artifact root
└── evaluation/
    ├── baselines/
    │   └── current.json
    ├── reviews/
    │   └── <run-id>.review.json
    └── reports/
        └── <timestamp>.json
```

### Pattern 1: Baseline as Deliberate Snapshot, Not Eval Side Effect

**What:** A baseline command should explicitly create or update a baseline artifact from an existing `EvalRunResult`/report only when the user asks for that action. `ood eval run` should remain an evaluation/report command, not an auto-promoter.

**When to use:** First baseline creation and later approved updates.

**Example:**

```python
# Source: project Phase 13 eval_report.py + Python json/pathlib docs
def save_observational_baseline(result: EvalRunResult, baseline_path: Path) -> None:
    payload = build_json_report(result)
    baseline_payload = {
        "schema_version": 1,
        "baseline_kind": "observational",
        "gate_mode": "review_required",
        "thresholds": None,
        "report": payload,
    }
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.write_text(
        json.dumps(baseline_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
```

### Pattern 2: Failed-Case Review Records are Derived Evidence + Human Decision

**What:** Generate review artifacts from failed and errored cases in a report. Each record should preserve expected sources, actual sources, mismatch metrics, query result evidence, proposed next action, and an explicit decision block.

**When to use:** After `ood eval run` produces failed/errored cases, before changing corpus/retrieval/baseline.

**Example:**

```python
# Source: project EvalCaseResult/eval_report schema
review_case = {
    "case_id": case["case_id"],
    "status": case["status"],
    "expected_sources": case["expected_sources"],
    "actual_sources": case["actual_sources"],
    "retrieval_metrics": case["retrieval_metrics"],
    "ticket_metrics": case["ticket_metrics"],
    "evidence": {
        "query": case["query"],
        "query_result": case["query_result"],
        "error": case["error"],
    },
    "proposed_next_action": "corpus_fix",  # corpus_fix | retrieval_fix | dataset_fix | baseline_update | investigate
    "decision": "deferred",                # approved | rejected | deferred
    "reviewer": None,
    "rationale": None,
    "reviewed_at": None,
    "baseline_update_status": "not_requested",
}
```

### Pattern 3: Review Gate as Predicate Over Decision Records

**What:** Baseline update and accepted-improvement commands should check for an explicit approved review decision before writing the new baseline or marking a change accepted.

**When to use:** Any operation that would replace `current.json`, accept corpus changes, accept retrieval changes, or declare a run as an improvement.

**Example:**

```python
# Source: locked Phase 14 D-07/D-08 decisions
def can_update_baseline(review: dict[str, object]) -> bool:
    return (
        review.get("decision") == "approved"
        and review.get("baseline_update_status") in {"approved", "requested"}
    )
```

### Pattern 4: CLI Output Boundary

**What:** Keep artifact JSON keys English, but render user-facing Typer messages in German. Use `dump_json_report`/artifact builders for machine output and separate helpers for human text.

**When to use:** All new `ood eval ...` commands.

**Example:**

```python
# Source: existing src/ood/eval_cli.py style
typer.echo("Baseline gespeichert: data/evaluation/baselines/current.json")
typer.echo("Review erforderlich: 2 fehlgeschlagene Fälle, 1 Fehler")
```

### Anti-Patterns to Avoid

- **Auto-promoting every eval report:** Violates D-01 and hides whether a user intentionally accepted the state.
- **Embedding thresholds in the first baseline:** Violates D-02; the first baseline is observed state, not a calibrated gate.
- **Adding new metric calculations in Phase 14:** Phase 12/13 own metrics; Phase 14 should consume report fields.
- **Updating baseline on metric improvement alone:** Violates D-08; require explicit approval.
- **Committing volatile reports by default:** `data/` is ignored and runtime artifacts should stay there unless a stable fixture/doc is intentionally created.
- **Putting review labels in Markdown knowledge:** Golden answers/eval truth stay in evaluation JSON/review artifacts, not indexed Markdown.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Evaluation execution | A second eval runner | `EvalRunner.run(...)` | Preserves black-box `RagEngine.query()` contract, skip/errored behavior, and `llm_used` metadata. |
| Report serialization | New report schema mapper | `build_json_report` / `dump_json_report` | Phase 13 locked schema_version=1 and key set/order; duplicating invites drift. |
| CLI grouping | Custom argparse / top-level commands | Existing Typer `eval_app` | Project already has Typer options, German strings, and reverse-import safety constraints. |
| Threshold gate | Hand-made hard pass/fail policy | Explicit review decision predicate | Hard thresholds are deferred; reviewed approval is the requirement. |
| Runtime artifact location | New committed report directory | Ignored `data/evaluation/...` defaults with path overrides | Keeps volatile reports out of git and aligns with `.gitignore`. |

**Key insight:** The hard part is not metrics; it is preserving intent. Baselines, reviews, and accepted improvements need provenance and explicit human decisions so future automation can tell the difference between “observed,” “investigating,” “accepted,” and “rejected.”

## Common Pitfalls

### Pitfall 1: Treating Baseline as a Hidden Threshold Gate

**What goes wrong:** The first baseline starts failing CLI runs or CI because current metrics are below an invented threshold.  
**Why it happens:** “Baseline” is confused with “regression gate.”  
**How to avoid:** Store `baseline_kind: observational`, `thresholds: null`, and keep normal failed cases as report content with exit 0.  
**Warning signs:** New code exits non-zero for `failed_count > 0` or compares metrics to fixed values.

### Pitfall 2: Review Artifacts Lack Enough Evidence to Act

**What goes wrong:** Reviewer sees a failed case but cannot tell whether to fix corpus, retrieval, dataset labels, or baseline.  
**Why it happens:** Artifact stores only `case_id` and status.  
**How to avoid:** Persist expected sources, actual sources with scores, mismatch metrics, query/result diagnostics, error snippet, proposed next action, and decision fields.  
**Warning signs:** Review JSON requires re-running eval to inspect what failed.

### Pitfall 3: Metric Improvement Bypasses Human Approval

**What goes wrong:** Better aggregate scores automatically replace the baseline even though a source is wrong, forbidden source appears, or labels changed incorrectly.  
**Why it happens:** Gate checks only summary numbers.  
**How to avoid:** Make baseline update command require an approved review artifact; rejected/deferred records must block.  
**Warning signs:** Code path named `if improved: save_baseline(...)`.

### Pitfall 4: Schema Drift Between Eval Report, Baseline, and Review

**What goes wrong:** Baseline parser expects fields that differ from report serializer or review artifacts re-key metrics.  
**Why it happens:** Duplicating `eval_report.py` mapping in new code.  
**How to avoid:** Embed or reference the existing report payload as-is; add wrapper metadata outside it.  
**Warning signs:** New code manually builds `meta`, `summary`, or `cases` from `EvalRunResult`.

### Pitfall 5: Circular Import Regression in `eval_cli.py`

**What goes wrong:** `from ood.eval_cli import eval_app` fails in a fresh process.  
**Why it happens:** New imports or command definitions move `eval_app = typer.Typer(...)` below `from ood.cli import ...`.  
**How to avoid:** Preserve Phase 13 import-safety ordering: define `eval_app` before importing helpers from `ood.cli`; add/keep subprocess import test.  
**Warning signs:** Decorators/imports are reorganized near the top of `eval_cli.py`.

### Pitfall 6: Knowledge-Dir Validation Surprises Tests and Case Listing

**What goes wrong:** CLI tests fail with missing source path errors before baseline/review code runs.  
**Why it happens:** `load_evaluation_dataset(..., knowledge_dir=...)` validates `expected_sources` against real Markdown files.  
**How to avoid:** Test fixtures must create stub Markdown for every expected source and pass `--knowledge-dir`.  
**Warning signs:** `EvaluationDatasetError: references missing knowledge source paths`.

## Code Examples

Verified patterns from project and official sources:

### Add Commands Without Breaking `eval_app` Import Safety

```python
# Source: src/ood/eval_cli.py and Typer subcommands docs
eval_app = typer.Typer(name="eval", help="Lokale Evaluation des OOD Agents über RagEngine.query().")

from ood.cli import KnowledgeDirOption, _load_valid_settings  # after eval_app definition

@eval_app.command("baseline")
def baseline(...):
    """Erzeuge oder aktualisiere eine beobachtende Baseline."""
```

### Write UTF-8 JSON Artifacts

```python
# Source: Python json docs; project eval_report.dump_json_report pattern
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
```

### Test Generated Artifacts with `tmp_path`

```python
# Source: pytest tmp_path docs and tests/test_eval_cli.py pattern
def test_baseline_writes_observational_snapshot(tmp_path: Path) -> None:
    baseline_path = tmp_path / "data" / "evaluation" / "baselines" / "current.json"
    save_baseline(result, baseline_path)
    payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    assert payload["baseline_kind"] == "observational"
    assert payload["thresholds"] is None
```

### Review Decision Gate

```python
# Source: Phase 14 D-07/D-08
APPROVED = "approved"

def require_approved_review(review: dict[str, object]) -> None:
    if review.get("decision") != APPROVED:
        msg = "Baseline-Update erfordert eine genehmigte Review-Entscheidung."
        raise EvalRunnerError(msg)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Ad-hoc `ood eval run --out` files as informal baselines | Explicit baseline snapshot flow | Phase 14 locked D-01 | Plans must add deliberate baseline commands, not rely on report files alone. |
| Failed case printed only in CLI human output | Machine-readable review artifact with evidence and decision fields | Phase 14 EVAL-11 | Plans must persist review JSON, not just print diagnostics. |
| Metric-only “improvement” acceptance | Explicit approved review decision | Phase 14 D-07/D-08 | Baseline updates must be gated by review status. |
| Hard thresholds/CI gates | Observational baseline with deferred threshold enforcement | v1.1 decision / future EVAL-10 | Do not introduce non-zero exit on failed eval cases. |

**Deprecated/outdated:**
- Phase 7-9 roadmap evaluation concepts are superseded by Phase 12-14. Use Phase 12 metric core, Phase 13 runner/report, and Phase 14 baseline/review scope.
- Auto-snapshotting every report was deferred out of Phase 13 and should not become implicit in Phase 14; snapshots must be deliberate.

## Open Questions

1. **Exact CLI command names and flags**
   - What we know: Must remain under `ood eval`; minimal cohesive surface preferred.
   - What's unclear: Whether planner chooses `baseline create/update`, `review create/decide`, or fewer commands.
   - Recommendation: Use a small surface: one command to create baseline from a run, one to generate review artifact from a report, one to apply/update baseline only with approved review.

2. **Canonical artifact format**
   - What we know: Machine-readable decision/evidence is required; JSON keys English; volatile runtime artifacts ignored by default.
   - What's unclear: Whether to add Markdown summaries.
   - Recommendation: JSON-only for Phase 14 implementation; add concise German CLI output. Markdown can be documented/deferred unless user explicitly wants human files.

3. **Granularity of approval**
   - What we know: Review records must support approved/rejected/deferred and baseline-update status.
   - What's unclear: Whether approval is per failed case, per report, or both.
   - Recommendation: Store per-case decisions and a top-level report decision. Baseline update should require top-level approved plus no blocking rejected/deferred cases marked as baseline-affecting.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| uv | Running tests/CLI in project environment | ✓ | 0.9.7 | none needed |
| Python via uv | Project runtime (`requires-python >=3.10`) | ✓ | uv-managed environment available; system `python3` is 3.9.6 | Use `uv run python`, not system `python3` |
| git | Optional provenance / docs workflow | ✓ | 2.33.0 | Omit git SHA if unavailable |
| Typer | CLI commands | ✓ | 0.25.1 | none recommended |
| pytest | Validation | ✓ | 9.0.3 | none recommended |

**Missing dependencies with no fallback:** None identified.

**Missing dependencies with fallback:** System `python3` is below project requirement; use `uv run` commands so the project-managed Python is used.

## Validation Architecture

Skipped because `.planning/config.json` has `workflow.nyquist_validation` explicitly set to `false`.

Recommended verification still exists for planner tasks:

- Quick CLI/unit run: `uv run pytest tests/test_eval_cli.py tests/test_eval_report.py -q`
- New baseline service run: `uv run pytest tests/test_eval_baseline.py -q` if planner creates that module.
- Full suite gate: `uv run pytest -q`.
- Import-safety check: `uv run python -c "from ood.eval_cli import eval_app; print('ok')"`.

## Sources

### Primary (HIGH confidence)

- `.planning/phases/14-baseline-feedback-loop-and-review-gate/14-CONTEXT.md` — locked Phase 14 decisions, scope, deferred items.
- `.planning/REQUIREMENTS.md` — EVAL-05 and EVAL-11 exact requirement text and traceability.
- `.planning/ROADMAP.md` — Phase 14 goal and success criteria.
- `.planning/STATE.md` — Phase 13 completion state, prior decisions, current next action.
- `.planning/phases/13-evaluation-service-and-cli-reporting/13-01-SUMMARY.md` — `EvalRunner` public dataclasses, pass/fail/skip/error behavior.
- `.planning/phases/13-evaluation-service-and-cli-reporting/13-02-SUMMARY.md` — locked `schema_version=1` JSON serializer contract.
- `.planning/phases/13-evaluation-service-and-cli-reporting/13-03-SUMMARY.md` — `ood eval` CLI surface, import-safety contract, German output, `--out` behavior.
- `src/ood/eval_cli.py` — existing Typer sub-app, flags, German formatter, import-safety ordering.
- `src/ood/eval_runner.py` — report source dataclasses and metrics/case status behavior.
- `src/ood/eval_report.py` — single JSON report serializer.
- `tests/test_eval_cli.py` — test fixtures, Typer CLI testing, knowledge-dir validation pattern.
- `pyproject.toml` — dependency and test configuration.
- `.gitignore` — `data/` ignored runtime artifact root.
- Python `json` official docs — `json.dumps`, `ensure_ascii`, `indent`, `json.loads`, order preservation: https://docs.python.org/3/library/json.html
- Typer official docs — command groups/subcommands and options: https://typer.tiangolo.com/tutorial/subcommands/ and https://typer.tiangolo.com/tutorial/options/
- pytest official docs — `tmp_path` fixture for temporary artifact tests: https://docs.pytest.org/en/stable/how-to/tmp_path.html

### Secondary (MEDIUM confidence)

- Installed package version probe via `uv run python` — confirms local versions but not upstream latest.

### Tertiary (LOW confidence)

- None used for critical claims.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new external stack; current project code and installed packages verified locally.
- Architecture: HIGH — directly constrained by Phase 13 public contracts and Phase 14 locked decisions.
- Pitfalls: HIGH — derived from existing Phase 13 summaries/tests and explicit Phase 14 anti-scope decisions.

**Research date:** 2026-05-11  
**Valid until:** 2026-06-10 for project-contract guidance; re-check Typer/pytest versions if dependency updates occur.
