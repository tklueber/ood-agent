# Project Research Summary

**Project:** OOD Agent  
**Domain:** Local-first Python CLI RAG assistant for German ServiceNow ticket triage  
**Milestone:** v1.1 Evaluations- und Real-Data, mockdata-first  
**Researched:** 2026-05-03  
**Confidence:** HIGH for local/mock/evaluation architecture; MEDIUM for later LightRAG/LLM threshold stability

## Executive Summary

OOD Agent v1.1 should become a measurable, mockdata-driven quality loop for the existing RAG assistant rather than a real-data integration milestone. Experts build this kind of system by separating curated test corpora, expected-output datasets, retrieval metrics, ticket-intelligence metrics, and privacy boundaries. For this project, the right v1.1 focus is extensive, clearly marked German mock Markdown knowledge that can be indexed like normal knowledge while remaining visibly synthetic and safe to commit.

The recommended approach is deliberately lightweight: keep the existing Python/Typer/RagEngine stack, add internal `ood.mockdata` and `ood.evaluation` modules, use JSON eval datasets/reports, and compute deterministic metrics with the standard library. Do not add Ragas, DeepEval, LangSmith, pandas, Faker, PyYAML, or LLM-as-judge infrastructure for the default v1.1 slice. Evaluate the public `RagEngine.query()` contract only, so fallback retrieval and LightRAG retrieval can be compared without coupling the harness to backend internals.

The main risks are false confidence and privacy leakage. Mock data can accidentally contain real tickets, be too easy for lexical retrieval, or leak golden-answer labels into indexed Markdown. Prevent this by enforcing `mock: true` metadata, using dedicated mock paths, scanning fixtures for PII/secrets/eval-label vocabulary, creating hard negative/paraphrased/noisy cases, running evals in fresh isolated storage, and keeping Cloud LLM usage off unless explicitly approved and opted in.

## Key Findings

### Stack Additions and Rejections

No runtime dependency additions are recommended for v1.1. The existing stack is sufficient if evaluation is implemented as small internal services and stable dataclass contracts.

**Core technologies:**
- Python `>=3.10` stdlib — deterministic generators, JSON/CSV reports, path handling, and metrics via `dataclasses`, `random.Random(seed)`, `pathlib`, `json`, `csv`, and `statistics`.
- Existing Typer CLI — add `ood mockdata`/`ood eval` command surfaces without introducing a separate runner.
- Existing `RagEngine` — reuse `reindex_markdown()` and `query()` as black-box behavior under test.
- Existing Pydantic/dataclass style — use only if schema diagnostics justify it; otherwise keep explicit dataclasses and validation.
- Existing pytest/tmp fixtures — validate generation, metrics, CLI JSON contracts, and clean isolated indexing.

**Explicit rejections for v1.1:**
- Ragas / DeepEval / TruLens / Phoenix / LangSmith dashboards — too heavy for deterministic local mock regression.
- Faker — domain-specific curated scenarios are more valuable than random realistic text.
- PyYAML / ruamel.yaml — avoid parser dependency unless already present; JSON is enough for eval fixtures.
- pandas / scikit-learn metrics — current metric tables are small and transparent with stdlib.
- Mandatory Cloud LLM judge — violates local-first/privacy-default behavior and makes CI flaky.

### Feature Table Stakes

**Must have:**
- Extensive mock corpus across Wiki, ServiceNow, Jira, runbooks, tickets, and notes; target 30-60 docs if feasible, with 15-25 dense docs as the minimum useful seed.
- Every mock document clearly marked in frontmatter and body, including `mock: true`, dataset marker, synthetic IDs, and visible mock warning text.
- German operational/domain language covering Police, Offerte, routing, ambiguous/noisy tickets, and command-risk examples.
- Import/index validation that exercises existing `index`, `reindex`, `update`, manifest, duplicate, stale-path, and metadata warning behavior.
- Versioned eval cases with expected sources, forbidden sources, routing, intent, identifiers, command risks, tags, and expected confidence/uncertainty behavior where relevant.
- Metrics report with retrieval metrics and deterministic ticket-intelligence metrics, emitted as JSON plus concise human/Markdown summaries.
- Local-first/offline default; no eval path should send ticket text to a Cloud LLM by default.

**Should have:**
- Mock-data safety validator for PII/secrets/real-looking identifiers and missing mock markers.
- Scenario coverage matrix by source type, system, component, route, risk, and case category.
- Golden-source debugging output that shows expected vs retrieved sources for failed cases.
- Separate scores for retrieval, routing, identifiers, command risk, confidence/uncertainty, and optional answer quality.
- Baseline comparison after the first stable run, once thresholds are grounded in observed metrics.

**Defer to v2+ / later milestone:**
- Real ServiceNow/Jira API import and production-data anonymization.
- Optional LLM-as-judge answer quality suite, pending privacy approval.
- Web UI, Teams integration, dashboards, tracing platforms, and generic experiment frameworks.
- Tool execution for command suggestions; keep classification-only behavior.

### Architecture Recommendations

Keep `RagEngine` focused on indexing/querying and add evaluation around it. v1.1 should introduce small, file-based services and result contracts rather than a new platform, database, or plugin system.

**Major components:**
1. `src/ood/models.py` — add `MockDataResult`, `EvalCase`, `EvalCaseResult`, `EvalMetrics`, and `EvalRunResult` with explicit `to_dict()` methods.
2. `src/ood/mockdata.py` — deterministic mock corpus generation and mock-only validation; writes normal Markdown with scalar frontmatter.
3. `src/ood/evaluation.py` — loads eval cases, calls `RagEngine.query()`, computes metrics from `QueryResult`, and returns stable run results.
4. `src/ood/cli.py` — expose `ood mockdata` and `ood eval run` with human/JSON output, path overrides, fresh storage defaults, and optional fail thresholds.
5. Fixture directories — prefer `knowledge/mock/v1.1/` for importable mock knowledge, `evaluation/v1.1/` or `tests/fixtures/evaluation/` for expected cases, and `data/eval/` for generated runtime reports.

**Key patterns:**
- Generate ordinary Markdown; existing index/update/reindex commands should need no mock-specific branches.
- Keep expectations outside indexed Markdown to prevent golden-answer leakage.
- Normalize paths and score exact relative source paths, not fuzzy matches or exact relevance scores.
- Use fresh isolated storage or clean reindex for every eval run.
- Record backend, dataset schema version, paths, counts, and `llm_used` in every report.

### Key Pitfalls and Prevention

1. **Real data leakage into mock fixtures** — enforce dedicated mock paths, mandatory mock frontmatter/body markers, fake IDs, and fixture privacy scans before commit/eval.
2. **Too-easy keyword evaluation** — include paraphrased, noisy, mixed-language, ambiguous, duplicate, stale/deprecated, no-answer, and hard-negative cases; do not rely on top-1 exact title matches.
3. **Retrieval-only false confidence** — report multi-axis metrics for retrieval, routing, intent, identifiers, command risk, and uncertainty; never collapse everything into one quality number.
4. **Golden-answer leakage** — keep eval expectations in JSON outside indexed Markdown and scan mock bodies for terms like `expected`, `golden`, `answer should`, or explicit route labels.
5. **Warning-only metadata hides poor corpus quality** — keep production indexing warning-only, but make the v1.1 mock validator fail on missing/invalid metadata and unknown controlled vocabulary.
6. **Stale index contamination** — eval must use temp/fresh storage or clean reindex and fail on sources not present in the current manifest.
7. **Cloud LLM changes privacy/determinism** — default eval must ignore/fail closed around LLM credentials unless `--allow-llm` is explicit and privacy-approved.

## Recommended Requirement Categories

1. **Mock Corpus and Safety** — corpus size, source-type coverage, German domain coverage, mandatory mock markers, fake identifiers, visible body warnings, and PII/secret scans.
2. **Import and Index Validation** — sample-data install/copy flow, idempotent generation/import, metadata validation, duplicate/stale diagnostics, manifest/source reconciliation, isolated storage.
3. **Evaluation Dataset Contract** — schema version, tagged cases, required/acceptable/forbidden sources, expected route/intent/IDs/risks, no-answer and uncertainty expectations.
4. **Metric and Report Contract** — Hit@1/3/5, MRR, source recall, forbidden-source rate, route/intent/identifier/risk accuracy, low-confidence/no-result rates, JSON/CSV/Markdown output.
5. **CLI and Developer Workflow** — `ood mockdata`, `ood eval run`, JSON/human output, README commands, example tickets, fixture-authoring guide, optional `--fail-under` after baseline.
6. **Privacy and LLM Governance** — default local-only eval, explicit `--allow-llm`, report `llm_used`, answer metrics marked N/A when no LLM is used.
7. **Baseline and Regression** — first run establishes baseline; later CI gates compare against baseline plus safety floors rather than arbitrary thresholds.

## Implications for Roadmap

The v1.1 phase outline should continue after completed Phase 5. The order below prioritizes data safety and corpus reliability before metrics and reporting.

### Phase 6: Mock Corpus Contract and Safety Foundation
**Rationale:** All later evaluation depends on safe, clearly synthetic, importable knowledge. Privacy mistakes are the highest-impact failure mode.  
**Delivers:** Mock metadata contract, controlled vocabulary, dedicated fixture paths, privacy/no-gaming scanner, deterministic generation or curated seed corpus.  
**Addresses:** MOCK-01, MOCK-02, MOCK-03; privacy-safe mock-data separation.  
**Avoids:** Real-data leakage, golden-answer leakage, metadata drift.  
**Research flag:** Standard patterns; no deeper research needed unless adding a third-party synthetic-data generator, which is not recommended.

### Phase 7: Mock Data Import and Index Validation
**Rationale:** Before scoring query quality, prove that the mock corpus behaves like normal knowledge through existing index/update/reindex paths.  
**Delivers:** Idempotent import/copy workflow, index smoke tests, metadata/duplicate/stale diagnostics, corpus summary report, fresh storage practices.  
**Addresses:** MOCK-04, import/index validation, mock-only guard.  
**Avoids:** Warning-only fixture quality, stale index contamination, accidental overwrite of non-mock files.  
**Research flag:** Standard patterns; validate LightRAG delete/update semantics only if incremental eval storage becomes necessary.

### Phase 8: Evaluation Dataset and Metric Core
**Rationale:** Expected cases and pure metric functions should be stable before adding CLI orchestration. They are deterministic and easy to unit test.  
**Delivers:** JSON eval schema, loader/validator, `EvalCase` models, metric functions for retrieval and ticket intelligence, hard-negative/paraphrase/noisy/safety case families.  
**Addresses:** EVAL-01, EVAL-03, EVAL-04; scenario coverage gate.  
**Avoids:** Keyword-only tests, retrieval-only false confidence, brittle exact-score thresholds.  
**Research flag:** Standard patterns for deterministic metrics; deeper research only if adopting external eval frameworks, which should be deferred.

### Phase 9: Evaluation Service and CLI Reporting
**Rationale:** Once data and metrics exist, orchestrate black-box queries through `RagEngine.query()` and expose results to developers/operators.  
**Delivers:** `EvaluationService`, `EvalRunResult`, `ood eval run`, JSON/CSV/Markdown reports, failed-case diagnostics, `llm_used` reporting, local-only default.  
**Addresses:** EVAL-02, EVAL-06, EVAL-07; developer workflow and report artifacts.  
**Avoids:** Cloud-LLM privacy drift, stale shared storage, opaque aggregate-only scores.  
**Research flag:** Needs targeted phase research if adding optional LLM answer-quality evaluation; otherwise standard implementation.

### Phase 10: Baseline, Documentation, and Regression Workflow
**Rationale:** Thresholds should come after an observed baseline, not before. Documentation turns the harness into a repeatable improvement loop.  
**Delivers:** Baseline report, smoke/full suite split, optional fail-under gates, README workflow, example queries, fixture-authoring guide, regression comparison plan.  
**Addresses:** EVAL-05, baseline gate, docs/developer usability.  
**Avoids:** Arbitrary thresholds, hidden failure modes, unmaintainable fixture growth.  
**Research flag:** Standard patterns; deeper research only when introducing CI provider-specific workflows or historical trend dashboards.

### Phase Ordering Rationale

- Safety and corpus contract must precede import/index validation because mock/real separation is foundational and hard to retrofit.
- Import/index validation must precede query evaluation because stale storage, metadata warnings, and duplicate drift can invalidate every metric.
- Eval schema and pure metrics should precede service/CLI work to keep scoring deterministic and easy to test.
- Baseline and regression gates belong last because thresholds are only meaningful after the first representative mock suite exists.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 9 optional LLM suite:** Requires privacy, prompt/eval, and model-specific research before answer-quality metrics or LLM-as-judge are accepted.
- **Phase 10 CI/trend dashboards:** Research only if moving beyond JSON/Markdown artifacts into hosted dashboards or historical analytics.
- **LightRAG incremental eval storage:** Research only if the implementation relies on update/delete semantics instead of fresh reindex storage.

Phases with standard patterns where `/gsd-research-phase` can be skipped:
- **Phase 6:** File fixtures, metadata contracts, deterministic generation, scanner tests.
- **Phase 7:** CLI/file import, pytest tmp dirs, manifest/index smoke validation.
- **Phase 8:** JSON schema loading and deterministic metric functions.
- **Phase 10 baseline docs:** README workflow, fixture authoring guide, baseline JSON artifact conventions.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Existing Python/Typer/RagEngine/pytest stack directly supports v1.1; official stdlib and Typer docs back the recommendation. MEDIUM only for LightRAG-specific runtime variability. |
| Features | HIGH | Table stakes come directly from milestone context and current project contracts; external RAG eval sources agree on dataset + metrics + component separation. |
| Architecture | HIGH | Current codebase boundaries were reviewed; recommended additions fit existing dataclass/service/CLI patterns. Metric thresholds remain MEDIUM until corpus exists. |
| Pitfalls | HIGH | Most risks are project-specific and visible in current behavior: warning-only metadata, optional LLM, fallback retrieval, manifest storage, and Markdown fixtures. |

**Overall confidence:** HIGH for the mockdata-first v1.1 roadmap; MEDIUM for future real-data/LLM evaluation details.

### Gaps to Address

- **LightRAG update/delete semantics:** Use fresh storage/reindex now; research before relying on incremental eval storage.
- **Metric thresholds:** Establish baseline first; do not invent hard gates before the mock suite is representative.
- **Eval case format final choice:** Prefer JSON to avoid dependency churn; choose YAML only if a parser is already present or explicitly accepted.
- **Privacy scanner patterns:** Start conservative and review false positives; expand patterns as fixtures grow.
- **Answer-quality evaluation:** Treat as optional and privacy-approved only; local mode should mark answer metrics as N/A.
- **Mock corpus realism:** Requires manual review to avoid both real-data leakage and keyword-overfit cases.

## Sources

### Primary (HIGH confidence)
- `.planning/research/STACK.md` — stack choices, avoided dependencies, metric/report recommendations.
- `.planning/research/FEATURES.md` — table stakes, differentiators, anti-features, requirement candidates.
- `.planning/research/ARCHITECTURE.md` — current architecture, new service boundaries, data flow, build order.
- `.planning/research/PITFALLS.md` — privacy, evaluation, metadata, stale-index, and LLM risks.
- Current repo context: `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `README.md`, `src/ood/*.py`, `tests/*.py`.
- Official Python docs for `json`, `csv`, and `statistics`; Typer command docs; pytest `tmp_path` docs.

### Secondary (MEDIUM confidence)
- Ragas metrics documentation — useful metric categories, not an implementation mandate.
- Promptfoo RAG evaluation guidance — retrieval/generation separation and citation assertions.
- LangSmith evaluation concepts — curated datasets, evaluators, baseline/regression framing.
- DeepEval and OpenAI Evals docs — conceptual support for test cases/graders; defer tooling adoption.

---
*Research completed: 2026-05-03*  
*Ready for roadmap: yes*
