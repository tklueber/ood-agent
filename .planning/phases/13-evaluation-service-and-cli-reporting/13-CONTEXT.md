---
phase: 13-evaluation-service-and-cli-reporting
status: ready-for-planning
created: 2026-05-10
requirements: [EVAL-02, EVAL-06, EVAL-07]
depends_on: [12-evaluation-dataset-and-metric-core]
---

# Phase 13: Evaluation Service and CLI Reporting — Context

**Gathered:** 2026-05-10
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a black-box evaluation runner that drives existing `EvaluationDataset` cases through the public `RagEngine.query()` contract (EVAL-02), aggregates retrieval and ticket-intelligence metrics, and emits reports in two forms: a human-readable CLI output and a structured JSON output (EVAL-06). Privacy posture stays observable through an explicit `llm_used` indicator in every report (EVAL-07).

**In scope:**
- New `ood eval` CLI namespace with subcommands (`run`, `cases`)
- Eval orchestration service: dataset → per-case `RagEngine.query()` → metric aggregation → report
- Human-readable output (German strings, header + summary + failure details)
- JSON schema with full per-case diagnostics + `meta` + `summary` blocks, versioned
- `llm_used` flag visible in the first header line of human output and in JSON `meta`
- Skip handling for cases that require LLM when LLM path is inactive

**Out of scope (deferred to Phase 14 or later):**
- Baseline persistence (Phase 14, EVAL-05)
- Feedback loop / review gate (Phase 14, EVAL-11)
- Hard pass/fail thresholds or CI gates (deferred to v2 — EVAL-10)
- LLM-as-judge scoring (deferred — EVAL-08)
- Historical baseline comparison or trends (deferred — EVAL-09)
- Web UI or hosted dashboards (project Out of Scope)

</domain>

<decisions>
## Implementation Decisions

### CLI Command Surface

- **D-01:** Use a `ood eval` subcommand namespace with `run` and `cases` as initial subcommands. Chosen over flat `ood evaluate` to leave room for Phase 14 extensions (`baseline`, `diff`, `review`) without naming churn.
- **D-02:** Default dataset path read from settings (`OOD_EVAL_DATASET`, with sensible default e.g. `evaluation/cases.json`), overridable per invocation via `--dataset <path>`. Mirrors the knowledge-dir pattern already in `Settings`.

### Report Output

- **D-03:** Human-readable output structure = Header (date, `llm_used`, retrieval backend, corpus hash) → aggregated Summary table (Hit@1/3/5, MRR, Source Recall, Forbidden-Source rate, Routing/Intent accuracy, Identifier F1) → Failure details only (expected vs actual). Pass cases shown only as a count, never enumerated.
- **D-04:** All user-facing strings in German (`Bestanden`, `Fehlgeschlagen`, `Cloud-LLM verwendet: nein`, etc.) to stay consistent with existing CLI commands like `ood query`. Metric keys in JSON remain English (`hit_at_1`, `mrr`) since they are international fachbegriffe.
- **D-05:** JSON schema = `{ schema_version: 1, meta: {...}, summary: {...}, cases: [...] }`. Per-case payload includes `query`, `expected_sources`, `actual_sources` (with scores), `match` flags, all retrieval and ticket-intelligence metrics, full `retrieval_diagnostics`, `analysis` (routing/intent/identifier/risk), and `llm_used`. Skill- and CI-tauglich. **No `--json-full` vs `--json` split — one schema only.**

### Cloud-LLM Activation in Eval (Privacy Gate)

- **D-06 (deliberate divergence from `ood query`):** Eval activates the Cloud-LLM path purely on **credential availability** (`has_llm_credentials`), without checking `OOD_ALLOW_CLOUD_LLM`. If credentials are present, LLM path is used; if absent, eval falls back to local extractive synthesis automatically. **This differs from `ood query` which requires both ENV + credentials.** Rationale: user wants frictionless eval with whatever LLM is configured; the privacy concern shifts to credential management instead of a runtime ENV gate.
- **D-07:** `llm_used: true|false` is rendered as the **second header line** of the human-readable output (right after the date/backend line), and at every level of the JSON (`meta.llm_used`, `summary.llm_used`, per-case `cases[i].llm_used`). When `llm_used` is `true`, the human header line is highlighted with a marker prefix (e.g. `»LLM«`) so reports can never be mistaken for local-only runs at a glance.
- **D-08:** Cases that declare an `expected_llm_answer` (or equivalent LLM-dependent expectation) are reported with `status: "skipped"` and `skip_reason: "llm_required"` when the LLM path is inactive. Skipped cases are excluded from pass/fail counts and from aggregated metrics — they appear in their own list. Prevents systematic false negatives.

### Exit-Code Policy

- **D-09:** `ood eval run` exits `0` on a successful run regardless of how individual cases fared. Exit code `≠0` is reserved for **hard errors only**: dataset file missing/unparseable, knowledge index missing, configuration invalid, unrecoverable code crash. Aligns with EVAL-05 (no arbitrary thresholds before a baseline exists). Phase 14 can introduce gating later.
- **D-10:** A single-case crash (e.g., `RagEngine.query()` raises) marks that case `status: "errored"` with a stacktrace snippet captured in the case payload, and the run **continues** for remaining cases. The lauf-level exit code stays `0` unless a hard error condition is hit. Avoids losing 49 case results because case 50 crashed.

### Claude's Discretion

- **Output destination:** stdout by default, optional `--out <path>` flag may be added if trivial — but auto-snapshotting under `evaluation/reports/<timestamp>.json` is **explicitly Phase 14 territory** (Baseline persistence). Planner picks the simplest stdout-first path.
- **Case filters:** `--case-id <id>` for single-case debugging is fine; richer filters (`--tag`, `--source`) deferred until dataset size demands them.
- **Engine reuse vs per-case isolation:** Planner decides. Simplest path: one `RagEngine` instance reused across cases for performance, but each query call is already stateless w.r.t. the index.
- **Determinism aids:** Capturing `git_sha`, `corpus_hash`, and dataset path/hash inside `meta` is encouraged but exact format up to planner.
- **Progress reporting during long runs:** Planner picks (silent vs single-line tick vs `--verbose`). Not a user-facing decision.
- **Error / log channel:** Planner picks how warnings/diagnostics flow (stderr vs structured field in JSON).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project Setup & Conventions
- `CLAUDE.md` — Project-level instructions (privacy posture, German UI strings, secrets via `.env`).
- `.planning/PROJECT.md` — Milestone v1.1 goals, Cloud-LLM privacy gate validated in Phase 10.
- `.planning/REQUIREMENTS.md` §EVAL-02, §EVAL-06, §EVAL-07 — exact requirement text and traceability table.

### Phase Dependencies
- `.planning/phases/12-evaluation-dataset-and-metric-core/` — Phase 12 plans and summaries (eval dataset schema, retrieval/ticket metric APIs).
- `.planning/phases/11-cli-grade-hybrid-retrieval-and-extractive-answer-synthesis/11-CONTEXT.md` — Hybrid retrieval contract that the eval runs against.
- `.planning/phases/10-echtes-lokales-embedding-retrieval-ohne-cloud-llm-aktivieren-und-llm-antwortsynthese-optional-privacy-gated-machen/` — Privacy-gate decisions for the Cloud-LLM path (`can_use_cloud_llm`, `has_llm_credentials`).

### Existing Code (must read before planning)
- `src/ood/rag.py` — `RagEngine.query()` is the public contract used by the eval. See `_aquery`, `QueryResult`, retrieval diagnostics shapes.
- `src/ood/evaluation.py` — `EvaluationDataset`, `EvaluationCase`, `load_evaluation_dataset` (Phase 12 deliverable).
- `src/ood/evaluation_metrics.py` — `evaluate_retrieval_case`, `summarize_retrieval_metrics`, `RetrievalCaseMetrics`, `RetrievalMetricsSummary`.
- `src/ood/evaluation_ticket_metrics.py` — Ticket-intelligence metric functions to reuse for routing/intent/identifier accuracy.
- `src/ood/cli.py` — Existing Typer command structure; new `ood eval` namespace must follow established patterns (`@app.command(...)`, German labels, `--storage-dir` style overrides).
- `src/ood/config.py` — `Settings` class; new `OOD_EVAL_DATASET` setting added here.
- `src/ood/models.py` — `QueryResult`, `SourceHit`, `TicketAnalysis`, `RetrievalDiagnostics` shapes that the JSON schema must mirror.

### Tests (existing patterns to follow)
- `tests/test_evaluation.py`, `tests/test_evaluation_metrics.py`, `tests/test_evaluation_ticket_metrics.py` — Phase 12 test conventions.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- **`RagEngine.query(query_text)` (src/ood/rag.py:84):** the public, stable entry point — the eval MUST go through this and only this. No internal helpers.
- **`load_evaluation_dataset(path)` (src/ood/evaluation.py:49):** ready-to-use dataset loader with knowledge-dir validation.
- **`evaluate_retrieval_case` + `summarize_retrieval_metrics` (src/ood/evaluation_metrics.py:59, 85):** retrieval Hit@k/MRR/recall pipeline ready.
- **Ticket-intelligence metric functions (src/ood/evaluation_ticket_metrics.py):** routing accuracy, intent accuracy, identifier F1, command-risk alignment.
- **Typer CLI patterns (src/ood/cli.py):** existing `@app.command()` registrations with German Echo strings and `--storage-dir` style overrides.
- **`Settings` (src/ood/config.py):** add `eval_dataset_path` here following the existing `OOD_*` ENV pattern.

### Established Patterns

- **JSON output for skill use:** `ood query --json` already emits structured output that ServiceNow / skill backends consume — eval JSON should follow the same nesting style.
- **German labels for human strings, English keys for JSON:** consistent across the existing CLI.
- **Privacy posture diagnostics:** `QueryResult.retrieval_diagnostics` already exposes `backend` and `strategy`; `analysis_mode` indicates whether LLM was used. Eval should hoist this into a `llm_used` boolean for clarity.

### Integration Points

- **CLI registration:** new `eval` Typer sub-app or grouped commands in `src/ood/cli.py`, importable from the top-level `app`.
- **Service module:** new `src/ood/eval_runner.py` (or similar) that owns the orchestration logic — separate from `evaluation.py` (data) and `evaluation_metrics.py` (calculation).
- **Config:** new `OOD_EVAL_DATASET` ENV var in `Settings`.

</code_context>

<specifics>
## Specific Ideas

- The `llm_used` indicator in human output should use a visible marker prefix when true (e.g. `»LLM«` or `⚠`). The exact glyph is planner-discretion but it MUST not be only color — terminals without color must still distinguish runs.
- The JSON `meta` block should at minimum include: `schema_version`, `run_started_at`, `run_finished_at`, `llm_used`, `retrieval_backend`, `dataset_path`, `dataset_hash`, `corpus_hash` (where computable), `git_sha` (where available), `command_args`.
- Cases with `expected_llm_answer` need a clear schema field — coordinate with Phase 12 dataset schema. If not present, planner adds it as optional.

</specifics>

<deferred>
## Deferred Ideas

- **Auto-snapshot reports to `evaluation/reports/<timestamp>.json`** — Belongs in Phase 14 baseline persistence (EVAL-05).
- **Historical comparison / diff between runs** — Phase 14 / EVAL-09 (deferred).
- **`--strict` mode that exits non-zero on case failures** — Effectively a CI gate, deferred to Phase 14 / EVAL-10.
- **Tag/source filters beyond `--case-id`** — Add when dataset grows; YAGNI now.
- **Progress bar / TUI during long runs** — Cosmetic, planner picks the minimum viable.
- **LLM-as-judge answer scoring** — EVAL-08 (deferred, requires separate privacy approval).
- **Reviewing the LightRAG architectural question (full LightRAG vs hybrid local)** — Tracked separately; the eval baseline produced here is the prerequisite to answer it factually.

</deferred>

---

*Phase: 13-evaluation-service-and-cli-reporting*
*Context gathered: 2026-05-10*
