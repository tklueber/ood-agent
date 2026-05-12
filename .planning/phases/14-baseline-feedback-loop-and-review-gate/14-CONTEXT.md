---
phase: 14-baseline-feedback-loop-and-review-gate
status: ready-for-planning
created: 2026-05-11
requirements: [EVAL-05, EVAL-11]
depends_on: [13-evaluation-service-and-cli-reporting]
---

# Phase 14: Baseline, Feedback Loop, and Review Gate - Context

**Gathered:** 2026-05-11
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 14 turns the existing local `ood eval run` report into an explicit baseline and review workflow. It must let the user save the first observed baseline without inventing hard pass/fail thresholds, generate review artifacts for failed cases, and require an explicit reviewer decision before corpus changes, retrieval changes, or baseline updates are accepted as improvements.

**In scope:**
- First baseline persistence for the existing `schema_version=1` evaluation report.
- Review artifacts for failed or errored cases with expected-vs-actual evidence.
- A local CLI workflow under the existing `ood eval` namespace for baseline, review, and update/apply actions.
- A review gate that records approved/rejected/deferred decisions before updates are accepted.
- Documentation for the local loop: generate/regenerate mock data, index, run smoke query, evaluate, review, and update baseline only when approved.

**Out of scope:**
- Arbitrary hard thresholds or CI regression enforcement before a stable baseline exists.
- Historical trend dashboards or hosted reporting.
- LLM-as-judge quality scoring.
- Real production data import or anonymization workflows.

</domain>

<decisions>
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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project and Requirements
- `.planning/PROJECT.md` - Current v1.1 milestone, local-first privacy posture, and validated Phase 13 state.
- `.planning/REQUIREMENTS.md` - EVAL-05 and EVAL-11 requirement text plus traceability to Phase 14.
- `.planning/ROADMAP.md` - Phase 14 goal, dependencies, and success criteria.
- `.planning/STATE.md` - Current project progress, prior decisions, and Phase 14 next-action notes.

### Phase Dependencies
- `.planning/phases/13-evaluation-service-and-cli-reporting/13-CONTEXT.md` - Phase 13 decisions, especially `ood eval` namespace, JSON schema, German human output, exit-code policy, and Phase 14 deferred items.
- `.planning/phases/13-evaluation-service-and-cli-reporting/13-01-SUMMARY.md` - EvalRunner public result types and runner behavior.
- `.planning/phases/13-evaluation-service-and-cli-reporting/13-02-SUMMARY.md` - JSON report serializer and `schema_version=1` wire schema.
- `.planning/phases/13-evaluation-service-and-cli-reporting/13-03-SUMMARY.md` - CLI command surface, `--out` behavior, German formatter, and Phase 14 readiness notes.
- `.planning/phases/12-evaluation-dataset-and-metric-core/` - Dataset and metric contracts consumed by the evaluation runner.

### Existing Code
- `src/ood/eval_cli.py` - Existing `ood eval run` and `ood eval cases` Typer sub-app; Phase 14 should extend this namespace and preserve import-safety constraints.
- `src/ood/eval_runner.py` - `EvalRunResult`, `EvalCaseResult`, `EvalRunMeta`, and `EvalRunSummary` dataclasses used as the source of report data.
- `src/ood/eval_report.py` - Single JSON serializer for `schema_version=1` reports; likely input for baseline snapshots.
- `src/ood/evaluation.py` - Evaluation dataset loading and validation behavior.
- `src/ood/config.py` - Settings patterns for `OOD_EVAL_DATASET` and path defaults.
- `tests/test_eval_cli.py`, `tests/test_eval_runner.py`, `tests/test_eval_report.py` - Existing test patterns for CLI, runner, and JSON output.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `EvalRunner.run(...)` already produces complete per-case results with statuses `passed`, `failed`, `skipped`, and `errored`, plus retrieval and ticket metrics.
- `dump_json_report(...)` is the single serializer for the existing wire schema and can seed baseline snapshots without inventing a second report shape.
- `ood eval run --out <path>` already writes JSON reports and creates parent directories; Phase 14 can build explicit baseline behavior on this rather than reimplementing report generation.
- `ood eval cases` can enumerate case IDs and may support review setup or sampling workflows.

### Established Patterns
- Human CLI output uses German labels, while JSON keys stay English.
- Hard CLI failures are reserved for run/config problems; normal failed evaluation cases still produce a report and exit 0.
- Privacy posture is surfaced via `llm_used` in the report, including a visible human marker when Cloud LLM was used.
- Generated runtime data and reports should generally stay out of git unless the planner intentionally creates stable fixtures or docs.

### Integration Points
- Add Phase 14 commands to `src/ood/eval_cli.py` while preserving the reverse-direction import safety comment/structure.
- Use `src/ood/eval_report.py` as the source of report serialization instead of duplicating schema mapping.
- Add focused tests beside existing eval tests, likely in `tests/test_eval_cli.py` and/or a new baseline/review test module.

</code_context>

<specifics>
## Specific Ideas

- The first baseline should be visibly labeled as observational, not a threshold gate.
- Review artifacts should make the human decision explicit enough that later agents can tell whether a failed case led to a corpus fix, retrieval fix, baseline update, rejection, or deferral.
- The planner has permission to choose exact command names and paths, but should keep them under `ood eval` and make the workflow easy to run locally.

</specifics>

<deferred>
## Deferred Ideas

- Hard CI regression gates with calibrated thresholds remain deferred to future EVAL-10 work.
- Historical trend comparison remains deferred until baseline mechanics and review decisions exist.
- LLM-as-judge answer scoring remains deferred and requires explicit privacy approval.

</deferred>

---

*Phase: 14-baseline-feedback-loop-and-review-gate*
*Context gathered: 2026-05-11*
