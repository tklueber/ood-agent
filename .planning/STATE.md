---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: Completed
status: complete
last_updated: "2026-05-11T19:06:46.700Z"
progress:
  total_phases: 13
  completed_phases: 13
  total_plans: 43
  completed_plans: 43
  percent: 100
---

# State: OOD Agent

**Last Updated:** 2026-05-11

---

## Project Reference

**Core Value:**
Operative Tickets werden durch intelligente Suche über verteilte Wissensquellen schneller gelöst – mit konkreten Handlungsempfehlungen, Quellenbelegen und Routing-Logik.

**Current Focus:**
Phase 16 — rag-backed-ood-skill-llm-synthesis-and-learning-loop

**Why This Matters:**
Die bisherigen Retrieval- und Evaluationsbausteine werden erst operativ wertvoll, wenn Supportmenschen sie direkt als Skill nutzen koennen: mit klarer Weiterleitung, aktuellem Diensthabenden, belegtem Loesungsvorschlag und einem Feedbackpfad, der spaetere echte Loesungswege in reviewbare Knowledge-Updates ueberfuehrt.

---

## Current Position

Phase: 16 (rag-backed-ood-skill-llm-synthesis-and-learning-loop) — COMPLETE
Plan: 05 complete
**Phase:** 16
**Plan:** 05 complete
**Status:** Complete
**Progress:** [██████████] 100%

**Milestone Goal:**
Das System als nutzbaren OOD-Support-Skill betreiben, der Routing, Kalender, RAG, privacy-gated LLM-Antworten und lernende Qualitätsrückmeldungen in einem Arbeitsfluss verbindet.

**Target Features:**

1. Installierbarer OOD-Incident-Skill nach Vorlage des bestehenden `06_OOD-KB/ood-agent` Skills
2. RAG per Projekt-Script als kanonische Skill-Quelle statt manueller Index-/Keyword-Suche
3. Deterministische Weiterleitungslogik mit Abteilung, SNOW-Hinweisen und OOD-Diensthabendem aus Kalendern
4. Privacy-gated LLM-Synthese fuer belastbare, quellengestuetzte Loesungsvorschlaege
5. Sofortiges Qualitaetsfeedback und asynchrone Ist-Loesung als Lernsignal mit review-gesteuerten Knowledge-Updates

---

## Performance Metrics

### Milestone-to-Date

**Efficiency:**

- Plans created: 8 for v1.1
- Plans completed: 8 for v1.1
- Plans abandoned: 0
- Repair cycles: 0

### Plan Execution Metrics

| Phase | Plan | Duration | Tasks | Files | Completed |
|-------|------|----------|-------|-------|-----------|
| 01-foundation-cli | 01 | 2min | 2 | 7 | 2026-05-01 |
| 01-foundation-cli | 02 | 1min | 2 | 4 | 2026-05-01 |
| 01-foundation-cli | 03 | 2min 22s | 2 | 4 | 2026-05-01 |
| 02-core-rag-engine | 01 | 5min 2s | 2 | 4 | 2026-05-01 |
| 02-core-rag-engine | 02 | 4min 14s | 2 | 2 | 2026-05-01 |
| 02-core-rag-engine | 03 | 2min 39s | 2 | 2 | 2026-05-01 |
| 02-core-rag-engine | 04 | 11min 7s | 3 | 4 | 2026-05-01 |
| 03-knowledge-management | 01 | 2min | 2 | 4 | 2026-05-01 |
| 03-knowledge-management | 02 | 2min | 2 | 2 | 2026-05-01 |
| 03-knowledge-management | 03 | 4min | 3 | 5 | 2026-05-01 |
| 04-ticket-intelligence | 01 | 2min | 2 | 4 | 2026-05-02 |
| 04-ticket-intelligence | 02 | 3min | 2 | 4 | 2026-05-02 |
| 04-ticket-intelligence | 03 | 3min | 2 | 3 | 2026-05-02 |
| 05-mock-corpus-contract-and-safety-foundation | 01 | 2min | 2 | 2 | 2026-05-03 |
| 05-mock-corpus-contract-and-safety-foundation | 02 | 1min | 2 | 2 | 2026-05-03 |
| 05-mock-corpus-contract-and-safety-foundation | 03 | 1min | 2 | 3 | 2026-05-03 |

**Quality:**

- v1.1 requirements mapped: 20/20
- v1.1 requirements validated: 11/20
- Requirements invalidated: 0
- Tests passing: 108 full project tests after Phase 12 completion

**Velocity:**

- v1.0 phases completed: 4/4
- v1.1 phases completed: 4/8
- Current next phase: Phase 16 planning for operational skill, LLM synthesis, and learning loop

| Phase 06-mock-data-import-and-index-validation P01 | 3min | 2 tasks | 1 files |
| Phase 06-mock-data-import-and-index-validation P02 | 3min | 3 tasks | 2 files |
| Phase 10-echtes-lokales-embedding-retrieval-ohne-cloud-llm-aktivieren-und-llm-antwortsynthese-optional-privacy-gated-machen P01 | 13min | 2 tasks | 4 files |
| Phase 10-echtes-lokales-embedding-retrieval-ohne-cloud-llm-aktivieren-und-llm-antwortsynthese-optional-privacy-gated-machen P02 | 8min | 2 tasks | 2 files |
| Phase 10-echtes-lokales-embedding-retrieval-ohne-cloud-llm-aktivieren-und-llm-antwortsynthese-optional-privacy-gated-machen P03 | 7min | 2 tasks | 5 files |
| Phase 11-cli-grade-hybrid-retrieval-and-extractive-answer-synthesis P01-03 | completed | 6 tasks | 7 files |
| Phase 12-evaluation-dataset-and-metric-core P01 | 10min | 2 tasks | 3 files |
| Phase 12-evaluation-dataset-and-metric-core P02 | 8min | 2 tasks | 2 files |
| Phase 12-evaluation-dataset-and-metric-core P03 | 10min | 2 tasks | 3 files |
| Phase 15-local-graph-metadata-retrieval-and-data-quality-review P01 | 20min | 2 tasks | 4 files |
| Phase 15-local-graph-metadata-retrieval-and-data-quality-review P02 | 18min | 2 tasks | 2 files |
| Phase 15-local-graph-metadata-retrieval-and-data-quality-review P04 | 14min | 2 tasks | 2 files |
| Phase 15-local-graph-metadata-retrieval-and-data-quality-review P03 | 10min | 2 tasks | 3 files |
| Phase 15-local-graph-metadata-retrieval-and-data-quality-review P05 | 16min | 2 tasks | 5 files |
| Phase 13-evaluation-service-and-cli-reporting P01 | 25min | 2 tasks | 6 files |
| Phase 13-evaluation-service-and-cli-reporting P02 | 2min | 1 tasks | 2 files |
| Phase 13-evaluation-service-and-cli-reporting P03 | 8min | 1 tasks | 3 files |
| Phase 14-baseline-feedback-loop-and-review-gate P01 | 2m 52s | 2 tasks | 2 files |
| Phase 14-baseline-feedback-loop-and-review-gate P02 | 3m 11s | 2 tasks | 2 files |
| Phase 14-baseline-feedback-loop-and-review-gate P03 | 2m 10s | 2 tasks | 3 files |
| Phase 16-rag-backed-ood-skill-llm-synthesis-and-learning-loop P01-05 | completed | 11 tasks | 13 files |

## Accumulated Context

### Decisions Made

- [Phase 01-foundation-cli]: Use uv with a committed uv.lock for reproducible local development.
- [Phase 01-foundation-cli]: Keep runtime indexes and local credentials outside git via data/ and .env ignores.
- [Phase 01-foundation-cli]: Use pydantic-settings with OOD_ env prefix and .env loading for Phase 1 configuration.
- [Phase 01-foundation-cli]: Keep missing Cloud LLM credentials valid in Phase 1 while exposing has_llm_credentials for later validation.
- [Phase 01-foundation-cli]: Derive storage_dir from the effective data_dir when no explicit storage override is supplied.
- [Phase 01-foundation-cli]: Expose ood.cli:app as the stable console script contract for downstream phases.
- [Phase 01-foundation-cli]: Keep Phase 1 commands as configuration-aware stubs and defer real indexing/query logic to Phase 2.
- [Phase 01-foundation-cli]: Use a flat Typer app with per-command shared options for JSON, verbosity, and path overrides.
- [Phase 02-core-rag-engine]: Keep LightRAG internals behind OOD-owned frozen dataclasses before service and CLI integration.
- [Phase 02-core-rag-engine]: Use environment markers so NumPy 2.4.4 is installed on Python 3.11+ while preserving project Python 3.10 resolution compatibility.
- [Phase 02-core-rag-engine]: Keep LightRAG construction behind RagEngine so CLI and future query logic do not depend on storage internals.
- [Phase 02-core-rag-engine]: Use a no-op LLM model function whenever credentials are absent so local indexing never sends content to a Cloud LLM.
- [Phase 02-core-rag-engine]: Scope clean rebuild deletion to children of Settings.storage_dir and preserve knowledge_dir plus sibling data files.
- [Phase 02-core-rag-engine]: Keep query output behind QueryResult so LightRAG result shapes do not leak into CLI contracts.
- [Phase 02-core-rag-engine]: Use naive LightRAG retrieval without credentials and mix mode only when LLM credentials are configured.
- [Phase 02-core-rag-engine]: Compute confidence deterministically from retrieval signals instead of relying on LLM self-rating.
- [Phase 02-core-rag-engine]: Keep CLI output rendering thin and driven by IndexResult and QueryResult dataclasses rather than LightRAG internals.
- [Phase 02-core-rag-engine]: Preserve the update command as the only remaining Phase 1 stub because incremental updates are out of Phase 2 scope.
- [Phase 02-core-rag-engine]: Use a local JSON fallback index when no LLM credentials are configured and the real LightRAG path would block CLI smoke usage.
- [Phase 03-knowledge-management]: Keep Phase 3 diagnostics in OOD-owned frozen dataclasses so CLI JSON stays independent from LightRAG internals.
- [Phase 03-knowledge-management]: Use warning-only metadata validation and strip YAML frontmatter before retrieval insertion.
- [Phase 03-knowledge-management]: Write ood-manifest.json for successful non-empty index/reindex runs and keep no-document runs as no-op without requiring a manifest.
- [Phase 03-knowledge-management]: Treat exact and near duplicates as reporting-only diagnostics so all documents remain indexable.
- [Phase 03-knowledge-management]: Use manifest content hashes to index only new and changed Markdown files while reporting deleted files as stale entries.
- [Phase 03-knowledge-management]: Expose update diagnostics through UpdateResult.to_dict() and keep CLI rendering thin.
- [Phase 03-knowledge-management]: Document ood reindex as the clean rebuild path for stale/deleted cleanup.
- [Phase 04-ticket-intelligence]: Keep trusted ticket fields deterministic and local so Phase 4 works without Cloud LLM credentials.
- [Phase 04-ticket-intelligence]: Represent intentional empty assessment and solution_steps in Plan 01 for later RAG/LLM enrichment.
- [Phase 04-ticket-intelligence]: Every RagEngine query path now computes analysis after retrieval confidence is scored.
- [Phase 04-ticket-intelligence]: LLM-backed answers only enrich assessment, solution_steps, and mode while deterministic labels remain unchanged.
- [Phase 04-ticket-intelligence]: Render human query output as operational triage sections while keeping JSON as result.to_dict().
- [Phase 04-ticket-intelligence]: Document that command risks are classified but never executed.
- [v1.1 Roadmap]: v1.1 starts with extensive mock data, not real or anonymized production data.
- [v1.1 Roadmap]: Preserve v1.0 completed phases 1-4 and continue v1.1 numbering at Phase 5.
- [v1.1 Roadmap]: Keep mock documents possibly in the system, but clearly marked with mandatory mock metadata, synthetic identifiers, and body warnings.
- [v1.1 Roadmap]: Run default evaluations locally without Cloud LLM usage and make `llm_used` explicit in reports.
- [v1.1 Roadmap]: Establish the first baseline before adding arbitrary hard regression thresholds.
- [Phase 05-mock-corpus-contract-and-safety-foundation]: Use dependency-free deterministic YAML-like scalar rendering so mock files follow the existing Phase 3 Markdown parser contract.
- [Phase 05-mock-corpus-contract-and-safety-foundation]: Keep generated Markdown free of expected answers and hidden labels so Phase 7 evaluation data remains separate from indexed knowledge.
- [Phase 05-mock-corpus-contract-and-safety-foundation]: Treat empty or missing corpora as warning-only validation results rather than crashes so CLI workflows remain actionable.
- [Phase 05-mock-corpus-contract-and-safety-foundation]: Keep safety validation local and deterministic with no Cloud LLM or external service calls.
- [Phase 05-mock-corpus-contract-and-safety-foundation]: Keep mock corpus operations as flat Typer commands to preserve the existing CLI contract.
- [Phase 05-mock-corpus-contract-and-safety-foundation]: Document that golden answers and expected sources belong in future evaluation JSON, never indexed Markdown.
- [Phase Phase 06-mock-data-import-and-index-validation]: Use RagEngine public index/reindex methods and local fallback mode to prove MOCK-04 without adding mock-specific production indexing logic.
- [Phase Phase 06-mock-data-import-and-index-validation]: Validate mock import through existing index, reindex, and update CLI commands with path overrides instead of adding mock-only index commands.
- [Phase 10-echtes-lokales-embedding-retrieval-ohne-cloud-llm-aktivieren-und-llm-antwortsynthese-optional-privacy-gated-machen]: Separate credential presence from Cloud LLM permission by keeping has_llm_credentials diagnostic-only and adding can_use_cloud_llm for any content-send path.
- [Phase 10-echtes-lokales-embedding-retrieval-ohne-cloud-llm-aktivieren-und-llm-antwortsynthese-optional-privacy-gated-machen]: Keep credentials-without-approval on retrieval-only/no-op LLM paths so configured secrets alone never enable answer synthesis.
- [Phase 10-echtes-lokales-embedding-retrieval-ohne-cloud-llm-aktivieren-und-llm-antwortsynthese-optional-privacy-gated-machen]: Supersede the lexical fallback artifact with ood-local-vector-index.json containing path, stripped content, excerpt, and vector fields.
- [Phase 10-echtes-lokales-embedding-retrieval-ohne-cloud-llm-aktivieren-und-llm-antwortsynthese-optional-privacy-gated-machen]: Return empty local fallback results for malformed vector payloads rather than crashing or downloading an embedding model unnecessarily.
- [Phase 10-echtes-lokales-embedding-retrieval-ohne-cloud-llm-aktivieren-und-llm-antwortsynthese-optional-privacy-gated-machen]: Expose cloud_llm_allowed only in verbose human output while keeping JSON exactly QueryResult.to_dict().
- [Phase 10-echtes-lokales-embedding-retrieval-ohne-cloud-llm-aktivieren-und-llm-antwortsynthese-optional-privacy-gated-machen]: Document OOD_ALLOW_CLOUD_LLM=false as the explicit privacy approval gate rather than implying credentials are enough.
- [Roadmap 2026-05-04]: Insert Phase 11 before evaluation because CLI answers should be skill-usable before building metrics and review gates around them.
- [Roadmap 2026-05-04]: Move hybrid retrieval out of deferred v2 scope into v1.1 as RAG-06 because exact IDs/codes need lexical signals alongside local embeddings.
- [Roadmap 2026-05-04]: Require local extractive answer synthesis before evaluation so default no-Cloud CLI output can be judged meaningfully.
- [Roadmap 2026-05-04]: Graph retrieval must either be truly enabled in local CLI queries or consciously deferred with activation criteria, not left ambiguous.
- [Roadmap 2026-05-04]: Evaluation follows as Phase 12-14 with dataset/metrics, CLI reporting, and a feedback loop with review gate.
- [Phase 11-cli-grade-hybrid-retrieval-and-extractive-answer-synthesis]: Expose retrieval diagnostics as an additive QueryResult field while preserving existing top-level JSON fields.
- [Phase 11-cli-grade-hybrid-retrieval-and-extractive-answer-synthesis]: Use deterministic hybrid local fallback scoring with semantic, lexical, and exact-operational-token boost components.
- [Phase 11-cli-grade-hybrid-retrieval-and-extractive-answer-synthesis]: Generate default no-Cloud answers from cited source excerpts rather than Cloud LLM synthesis.
- [Phase 11-cli-grade-hybrid-retrieval-and-extractive-answer-synthesis]: Defer graph retrieval until a deterministic local graph artifact and privacy-safe tests exist.
- [Phase 12-evaluation-dataset-and-metric-core]: Keep evaluation labels in versioned JSON outside indexed Markdown so mock knowledge remains retrieval input only.
- [Phase 12-evaluation-dataset-and-metric-core]: Validate expected and forbidden source paths as portable POSIX-relative paths before evaluation execution.
- [Phase 12-evaluation-dataset-and-metric-core]: Compute retrieval metrics only from EvaluationCase and ordered SourceHit.path values, keeping retrieval backends black-box for Phase 13.
- [Phase 12-evaluation-dataset-and-metric-core]: Deduplicate returned paths for recall and forbidden checks while preserving first rank for Hit@k and MRR.
- [Phase 12-evaluation-dataset-and-metric-core]: Compare ticket metrics only against public TicketAnalysis output rather than duplicating raw-ticket analysis rules.
- [Phase 12-evaluation-dataset-and-metric-core]: Document Phase 12 as dataset and pure metric core only; Phase 13 owns CLI execution through RagEngine.query().
- [Roadmap 2026-05-08]: Preserve Phase 13 evaluation service/CLI reporting and Phase 14 baseline/review scope as-is; add local graph/metadata retrieval as Phase 15 after those planned phases.
- [Roadmap 2026-05-08]: Treat the TraceId/Kafka rank-4 miss as evidence that hybrid semantic+lexical retrieval needs explainable metadata/graph signals and source-data quality review.
- [Roadmap 2026-05-08]: Evaluate the Obsidian OOD-KB article corpus quality explicitly before making graph/metadata boosts default behavior.
- [Phase 15-local-graph-metadata-retrieval-and-data-quality-review]: Keep graph metadata extraction dependency-free and derived only from Markdown/frontmatter/Wikilinks.
- [Phase 15-local-graph-metadata-retrieval-and-data-quality-review]: Preserve the existing SourceScoreBreakdown constructor by adding graph and metadata fields after existing fields with defaults.
- [Phase 15-local-graph-metadata-retrieval-and-data-quality-review]: Use conservative local-only fusion weights with metadata and graph signals strong enough to lift operationally tagged articles above body-similar noise.
- [Phase 15-local-graph-metadata-retrieval-and-data-quality-review]: Keep missing or malformed graph artifacts as semantic+lexical fallback with explicit diagnostics rather than query failure.
- [Phase 15-local-graph-metadata-retrieval-and-data-quality-review]: Keep source-data quality audits independent from indexing so the external OOD-KB can be reviewed without Cloud LLM or vector artifacts.
- [Phase 15-local-graph-metadata-retrieval-and-data-quality-review]: Treat recommendations as actionable Markdown edits with document or corpus scope instead of raw metric-only findings.
- [Phase 15-local-graph-metadata-retrieval-and-data-quality-review]: Keep query JSON unchanged as QueryResult.to_dict() while rendering CLI-only readability improvements only in verbose human output.
- [Phase 15-local-graph-metadata-retrieval-and-data-quality-review]: Write quality-audit reports only when users provide --report-path and keep recommended report paths under ignored data/.
- [Phase 15-local-graph-metadata-retrieval-and-data-quality-review]: Treat the TraceId/Kafka smoke fixture as an external OOD-KB case, not part of the synthetic mock corpus.
- [Phase 13-evaluation-service-and-cli-reporting]: Eval activates Cloud-LLM on Settings.has_llm_credentials alone (D-06); EvalRunner._engine_settings forges effective Settings via model_copy so the engine's internal privacy gate flips True end-to-end without mutating caller Settings.
- [Phase 13-evaluation-service-and-cli-reporting]: IndexMissingError raised by RagEngine.query bubbles out of EvalRunner.run unchanged for CLI exit-1 mapping (D-09); any other per-case exception is captured as status=errored with a stacktrace snippet and the run continues (D-10).
- [Phase 13-evaluation-service-and-cli-reporting]: Settings.eval_dataset_path uses pydantic AliasChoices to honor the documented OOD_EVAL_DATASET env var despite the OOD_ env_prefix that would otherwise expect OOD_EVAL_DATASET_PATH.
- [Phase 13-evaluation-service-and-cli-reporting]: Plan 02 ships a single JSON wire-schema serializer (build_json_report / dump_json_report) used by both stdout and --out paths in Plan 03 — no --json vs --json-full split (D-05); metric dicts flow through unchanged with English keys (D-04).
- [Phase 13-evaluation-service-and-cli-reporting]: Skipped and errored cases keep their slot in the JSON cases array with retrieval_metrics/ticket_metrics/query_result serialized as null rather than omitted, so downstream consumers see a stable per-case key set (D-08 / D-10).
- [Phase 13-evaluation-service-and-cli-reporting]: Plan 03 ships ood eval run/cases CLI: German human formatter with »LLM« marker (D-07), single JSON wire-schema via Plan 02 serializer (D-05), exit-code policy 0 on successful run regardless of pass/fail and 1 on hard errors including IndexMissingError mapped to German message (D-04/D-09); pass cases never enumerated (D-03), skipped/errored isolated in own sections (D-08/D-10).
- [Phase 13-evaluation-service-and-cli-reporting]: Reverse-direction circular-import safety pattern: define eval_app = typer.Typer(...) BEFORE the from ood.cli import (...) statement in eval_cli.py so cli.py's bottom-of-file deferred 'from ood.eval_cli import eval_app' survives the partial-load re-entry that fires DURING eval_cli's own import-statement execution (not during decorator execution).
- [Phase 14-baseline-feedback-loop-and-review-gate]: Keep Phase 14 Plan 01 as a pure stdlib artifact layer: no CLI wiring, no new dependencies, no metric recomputation.
- [Phase 14-baseline-feedback-loop-and-review-gate]: Represent first baselines as observational snapshots with thresholds: null and gate_mode: review_required rather than hard pass/fail thresholds.
- [Phase 14-baseline-feedback-loop-and-review-gate]: Require an approved review, reviewer identity, and requested/approved baseline_update_status before can_update_baseline returns true.
- [Phase 14-baseline-feedback-loop-and-review-gate]: Keep baseline creation as an explicit ood eval baseline --report user action rather than auto-promoting ood eval run --out reports.
- [Phase 14-baseline-feedback-loop-and-review-gate]: Expose the allowed proposed-fix vocabulary in ood eval review --json so downstream review-gate workflows can preserve machine-readable fix intent.
- [Phase 14-baseline-feedback-loop-and-review-gate]: Keep baseline updates as explicit, review-gated CLI actions; metric improvement alone never updates current.json.
- [Phase 14-baseline-feedback-loop-and-review-gate]: Preserve per-case proposed_fix_type and proposed_fix_notes while applying top-level review decisions and baseline update state.
- [Phase 16]: Forwarded PKV/KMU incidents now short-circuit before RAG or Cloud LLM synthesis.
- [Phase 16]: Operational Cloud LLM exposure remains gated by Settings.can_use_cloud_llm while feedback/resolutions create pending proposals only.

### Roadmap Evolution

- Phase 10 added: Echtes lokales Embedding-Retrieval ohne Cloud-LLM aktivieren und LLM-Antwortsynthese optional privacy-gated machen
- Phase 11 added: CLI-Grade Hybrid Retrieval and Extractive Answer Synthesis
- Phase 7-9 evaluation concepts superseded by Phase 12-14 so retrieval quality work happens first and the feedback loop includes an explicit review gate.
- Phase 15 added: Local Graph-/Metadata Retrieval and Data Quality Review after the existing Phase 13/14 evaluation loop.
- Phase 16 added: RAG-backed operational OOD skill with routing/calendar hand-off, privacy-gated LLM synthesis, immediate quality feedback, asynchronous actual-resolution capture, and reviewed knowledge-update proposals.

### Open Todos

No open Phase 16 todos — operational skill, routing/calendar contracts, synthesis, feedback capture, asynchronous resolution learning, and reviewed knowledge-update generation are implemented.

### Current Blockers

No blockers — Phase 16 is ready to plan.

### Recent Learnings

- NumPy 2.4.4 requires Python >=3.11, so Python 3.10-compatible projects need environment markers or a lower fallback pin.
- v1.1 should be mockdata-first because privacy-safe measurement is needed before real/anonymized production data.
- Phase 5 mock Markdown generation and validation can stay fully local and deterministic while preserving later evaluation separation.
- Evaluation truth belongs in versioned JSON outside indexed Markdown so retrieval input and answer labels stay separated.
- Metric cores should compare public contracts (`SourceHit`, `TicketAnalysis`) rather than retrieval or analysis internals.

---

## Session Continuity

**Last Session:** 2026-05-11T19:06:46.696Z

**What Just Happened:**

- Completed Phase 14 Plan 03: added `ood eval decide` and `ood eval update-baseline` under the existing eval CLI namespace.
- Review decisions now support approved/rejected/deferred outcomes while preserving per-case `proposed_fix_type` and `proposed_fix_notes` values.
- Baseline updates now require `can_update_baseline(review)` and mark the top-level review `baseline_update_status` as `updated` only after a successful observational baseline write.
- README now documents the local mock-init → reindex → smoke query → eval → baseline → review → decide → update-baseline loop and reinforces that metric improvement alone is not accepted improvement.
- Verification: `uv run pytest tests/test_eval_cli.py tests/test_eval_baseline.py -q` passed with **60 tests**; import smoke printed `ok`; `uv run ood eval --help` lists the new commands.

**Next Action:**
Run the Phase 14 verifier and then transition the completed phase if verification passes.

**On Deck:**

- Phase 14: Baseline, Feedback Loop, and Review Gate
- Phase 15: Local Graph-/Metadata Retrieval and Data Quality Review

---

## Key Files

**Planning:**

- `.planning/PROJECT.md` — Core value, constraints, evolution log
- `.planning/REQUIREMENTS.md` — v1.1 requirements and traceability
- `.planning/ROADMAP.md` — Phase structure, success criteria
- `.planning/STATE.md` — This file (current position, context)

**Implementation:**

- `knowledge/` — Markdown knowledge base and future mock corpus location
- `evaluation/` — Future versioned evaluation datasets and report fixtures
- `.env` — Cloud LLM credentials (must not be committed)
- `data/` — Persistent index and evaluation runtime data (outside git)

---

*State checkpoint: 2026-05-08 after adding Phase 15 local graph/metadata retrieval and OOD-KB data-quality review*
