# Domain Pitfalls: v1.1 Mockdata-Driven Evaluation

**Project:** OOD Agent  
**Milestone:** v1.1 Evaluations- und Real-Data  
**Researched:** 2026-05-03  
**Scope:** Extensive mock knowledge corpus, import/index validation, and evaluation metrics for an existing local Python CLI RAG assistant.  
**Overall confidence:** HIGH for project-specific pitfalls based on current code/tests; MEDIUM for broader RAG-evaluation practices verified against Ragas and LangSmith docs.

## Executive Warning

The largest v1.1 risk is not that evaluation is missing; it is that the team builds an evaluation harness that looks objective but mostly proves the mock fixtures are easy. OOD currently has deterministic fallback retrieval, warning-only metadata validation, source scoring heuristics, deterministic routing, and optional Cloud-LLM behavior. The evaluation milestone must therefore test the real contracts: indexed Markdown quality, source-hit correctness, routing/identifier/risk outputs, privacy boundaries, and regression behavior across both local-only and optional LLM modes.

The second critical risk is contaminating the repo with real ticket content while trying to create realistic data. Because Markdown is the canonical knowledge unit and `knowledge/` may be committed, v1.1 needs explicit mock labeling, fake identifiers, fixture scanners, and path separation from any future real exports.

## Critical Pitfalls

### Pitfall 1: Mock Data Accidentally Contains Real Ticket or Customer Data

**What goes wrong:** Real ServiceNow/Jira/wiki snippets, customer names, policy/offerte numbers, internal URLs, emails, secrets, or operational commands are copied into mock Markdown because they are convenient and realistic.

**Why it happens in this project:**
- Markdown sources are human-editable and easy to commit.
- Current metadata validation checks required fields and `status`, but does not enforce `mock: true`, synthetic IDs, PII absence, or corpus classification.
- Runtime `data/` is excluded from git, but source fixtures under a future mock corpus are likely intended to be versioned.

**Consequences:**
- Privacy breach before Cloud-LLM approval.
- Evaluation results cannot be safely shared or committed.
- Future Cloud-LLM evaluation could send real ticket text externally if credentials are configured.

**Warning signs:**
- Mock files contain realistic names, emails, phone numbers, hostnames, URLs, full stack traces, real-looking policy/offerte numbers, or environment names.
- Frontmatter only has the current required fields (`quelle`, `datum`, `status`, `system`, `komponente`, `title`, `type`) and no explicit synthetic-data marker.
- Tests assert retrieval against files under generic `knowledge/` instead of a clearly named mock fixture directory.
- Evaluation tickets use copied production wording rather than synthetic scenarios.

**Prevention:**
- Add mandatory frontmatter for v1.1 mock fixtures: `mock: true`, `dataset: v1.1-mock`, `synthetic: true`, `sensitivity: public-test`, and stable `case_id`.
- Keep committed mock data in a dedicated path such as `knowledge/mock/v1_1/` or `tests/fixtures/knowledge/mock_v1_1/`; never mix with future real exports.
- Add a privacy scanner test over all committed mock Markdown and eval JSON/YAML files for emails, phone numbers, private keys, common secret prefixes, internal domains, and forbidden real identifiers.
- Use obviously fake IDs (`POL-MOCK-1001`, `OFF-MOCK-2001`, `INC-MOCK-3001`, `JIRA-MOCK-4001`) rather than production-like numbers.
- Force evaluation runs to default to local/retrieval-only mode unless an explicit opt-in flag is passed.

**Phase / requirement implications:**
- Address in the first v1.1 phase before importing/indexing tests.
- Maps to active requirements: mock data provision, mock-data separation, privacy-safe import flow.

**Concrete quality gates:**
- `uv run pytest` includes a fixture privacy test that fails if committed mock/eval files contain likely PII/secrets or missing mock markers.
- Every mock Markdown document has required base metadata plus mock-specific metadata.
- No evaluation command sends ticket text to a Cloud LLM by default; JSON output for eval cases records `llm_used: false` in the default suite.

---

### Pitfall 2: Evaluation Dataset Is Too Easy and Rewards Keyword Matching

**What goes wrong:** Queries and expected sources share exact titles, IDs, and uncommon terms. The local fallback retriever in `RagEngine._query_local_fallback()` scores token overlap, so such tests can pass even when semantic retrieval, ambiguity handling, and routing are weak.

**Why it happens in this project:**
- Current fallback scoring gives high scores based on term overlap and rank.
- Existing tests use tiny corpora and direct phrases like “Restart worker”.
- The v1.1 goal asks for extensive mock data, which can create volume without actual retrieval difficulty.

**Consequences:**
- High hit rate with poor real-world usefulness.
- Roadmap falsely concludes retrieval quality is validated.
- Later real/anonymized data causes a quality drop and possibly architectural churn.

**Warning signs:**
- Most expected hits are retrieved because the query repeats the document title.
- Evaluation only checks top-1 source path and ignores distractors.
- No cases with synonyms, German/English variation, abbreviations, typos, stale/deprecated docs, duplicate docs, or mixed Police/Offerte context.
- Metrics improve when adding more exact IDs but not when paraphrasing queries.

**Prevention:**
- Design eval cases in families: exact, paraphrased, noisy ticket text, mixed-language, ambiguous, duplicate/stale conflict, no-answer, and command-risk cases.
- Include hard negatives: plausible but wrong runbooks, deprecated articles, near duplicates, and unrelated incidents with overlapping tokens.
- Require expected source sets, not only one golden path: `must_retrieve`, `acceptable_retrieve`, `must_not_retrieve`.
- Evaluate at `top_k` boundaries already used by OOD (`top_k=10`) with Hit@1, Hit@3, MRR, and “forbidden-source retrieved” checks.

**Phase / requirement implications:**
- Address during eval dataset design before metric implementation.
- Maps to active requirements: evaluation dataset with expected sources, import/indexing realistic check.

**Concrete quality gates:**
- At least 30–40% of eval tickets are paraphrased/noisy and do not repeat the target title.
- Every scenario includes at least one distractor document.
- Eval report separates exact-match cases from paraphrase/noisy cases.
- A failure is raised if any `must_not_retrieve` source appears above a configured rank threshold.

---

### Pitfall 3: Metrics Create False Confidence Because They Measure Only Retrieval

**What goes wrong:** v1.1 reports only retrieval scores while OOD’s value proposition also depends on routing, ID extraction, command-risk classification, uncertainty reporting, and grounded solution steps.

**Why it happens in this project:**
- Existing code has separate contracts: `sources`, `confidence`, and nested `analysis` (`intent`, `routing`, `identifiers`, `command_risks`, `uncertainties`).
- Retrieval metrics like context precision/recall are common in RAG tooling, but they do not validate ticket-intelligence decisions by themselves. Ragas documents RAG metrics such as context precision/recall, faithfulness, response relevancy, and noise sensitivity; LangSmith documents datasets plus code, human, and LLM-as-judge evaluators.

**Consequences:**
- A query can retrieve the right document but route to the wrong team or miss a red command.
- Confidence scores may look high while the operational decision is unsafe.
- Roadmap phases optimize vector retrieval instead of ticket-assistance quality.

**Warning signs:**
- Evaluation output has aggregate Hit@K only.
- No assertions for `analysis.routing.route`, extracted police/offerte IDs, command risk labels, or uncertainties.
- Cases with no sources or low confidence are scored as “bad retrieval” but not checked for correct `Rückfrage` behavior.

**Prevention:**
- Treat evaluation as a multi-axis contract test:
  - Retrieval: Hit@K, MRR, forbidden-source rate.
  - Ticket intelligence: intent accuracy, route accuracy, identifier F1/exact match, command-risk label accuracy.
  - Safety behavior: uncertainty present for no/low evidence, no command execution, red/orange commands never hidden.
  - Optional answer quality: groundedness/faithfulness only when LLM mode is explicitly enabled.
- Report metrics per axis and per scenario type; never collapse into one “quality” number.

**Phase / requirement implications:**
- Address when defining evaluation schema and CLI/report output.
- Maps to active requirements: evaluation dataset with expected routing/risks and quality metrics for retrieval and ticket intelligence.

**Concrete quality gates:**
- Eval case schema includes expected `intent`, `route`, `identifiers`, `command_risks`, `must_retrieve`, and `must_not_retrieve`.
- CI fails if route accuracy or red-command recall drops below a strict threshold, even when retrieval passes.
- Report shows separate sections for Retrieval, Routing, Identifier Extraction, Command Risk, Confidence/Uncertainty.

---

### Pitfall 4: Evaluation Gaming Through Golden Answers Leaking Into Corpus

**What goes wrong:** Mock documents contain the same phrasing as expected answers or explicit labels like “expected route: weiterleiten Policen”, so retrieval and answer metrics are gamed.

**Why it happens in this project:**
- Markdown is flexible and frontmatter/body are currently stripped/indexed in a simple way: frontmatter is removed, but body text is fully indexed.
- Evaluation authors may write runbooks after writing expected outputs.
- The fallback index stores raw body content in JSON under storage.

**Consequences:**
- Evaluation proves the model can copy test labels, not infer from evidence.
- Later real data fails because real documents do not include evaluation hints.

**Warning signs:**
- Body text includes “route to”, “expected”, “golden”, “evaluation”, “answer should”, or exact expected solution-step language.
- Expected source document and expected answer are authored in the same commit without review.
- Very high response relevance but weak source diversity.

**Prevention:**
- Keep evaluation expectations outside indexed Markdown, e.g. `tests/fixtures/eval_cases/*.json`.
- Add a scanner that rejects evaluation-label vocabulary in indexed mock bodies.
- Use document content that resembles operational knowledge, not answer rubrics.
- Create eval cases after corpus creation or have a separate review pass to remove leakage.

**Phase / requirement implications:**
- Address during corpus authoring and eval schema design.

**Concrete quality gates:**
- Test fails if indexed mock Markdown body contains forbidden evaluation-label terms.
- Eval expectations are never discovered by `_discover_markdown_files()` for a given eval run.
- At least one reviewer check or automated snapshot confirms only knowledge docs are indexed.

---

### Pitfall 5: Mock Corpus Lacks Metadata Quality, But Warnings Stay Non-Blocking

**What goes wrong:** The system indexes files with missing/invalid metadata because warnings are reporting-only. Evaluation then measures retrieval over a corpus that would be unacceptable as curated knowledge.

**Why it happens in this project:**
- `RagEngine._metadata_warnings()` reports missing `quelle`, `datum`, `status`, `system`, `komponente`, `title`, and `type`, but indexing continues.
- Existing tests explicitly validate that metadata warnings are non-blocking.
- v1.1 depends on metadata to distinguish tickets/wiki/Jira/ServiceNow and mock vs future real data.

**Consequences:**
- Mock/real separation relies on convention rather than enforceable data contracts.
- Evaluation cannot segment by source type, system, component, date, or status.
- Deprecated/draft documents may be treated like active ones.

**Warning signs:**
- Eval imports pass while `metadata_warnings` is non-empty.
- Mock documents use inconsistent `type` values (`ticket`, `servicenow`, `case`, `incident`) without a controlled vocabulary.
- Reports cannot answer “which source type failed?”

**Prevention:**
- Keep runtime indexing warning-only, but make the v1.1 mock-corpus validator fail on metadata warnings.
- Define controlled metadata values for v1.1: source type (`wiki`, `servicenow_case`, `jira_bug`, `ticket`, `note`), status (`active`, `deprecated`, `draft`), mock markers, and component taxonomy.
- Add a corpus summary report with counts by `type`, `system`, `komponente`, `status`, duplicates, skipped docs, and warnings.

**Phase / requirement implications:**
- Address during import/index validation phase.
- Maps to active requirements: extensive mock knowledge base, import/index validation, mock-data distinction.

**Concrete quality gates:**
- v1.1 corpus validation fails on any metadata warning in committed mock data.
- Eval report records zero skipped mock documents unless intentionally listed in a negative test.
- Controlled vocabulary test rejects unknown `type`, missing `mock`, or invalid `status`.

---

### Pitfall 6: Stale Index Entries Pollute Evaluation Runs

**What goes wrong:** Deleted/renamed mock documents remain in storage and still influence retrieval, especially when `ood update` reports `stale_entries` but does not delete LightRAG entries.

**Why it happens in this project:**
- Current update behavior reports deleted paths and instructs users to run `ood reindex` for cleanup.
- `index` does not clear existing storage; only `reindex` does.
- Evaluation runs may reuse `data/storage` between iterations.

**Consequences:**
- Metrics are non-reproducible and may pass due to documents no longer present in the corpus.
- Debugging failed retrieval becomes confusing because sources can come from stale storage.

**Warning signs:**
- Eval run uses `ood update` instead of clean `ood reindex`.
- Source paths appear in results but not in the current mock corpus.
- Metrics differ depending on local developer state.

**Prevention:**
- Evaluation harness must use a fresh temporary storage directory per run or explicitly call clean `reindex` into an isolated path.
- After indexing, compare returned sources against the current manifest entries and fail on unknown paths.
- Store eval artifacts under a dedicated ignored runtime directory, not the default shared `data/storage`.

**Phase / requirement implications:**
- Address in import/index validation and eval-run implementation.

**Concrete quality gates:**
- Eval harness creates and deletes a temp storage dir or writes to `data/eval/<run_id>/storage`.
- Eval fails if `diff.deleted_paths` is non-empty or if any result source path is absent from the fresh manifest.
- CI eval starts from an empty storage directory.

---

### Pitfall 7: Cloud-LLM Evaluation Violates Privacy or Changes Deterministic Contracts

**What goes wrong:** Developers run evals with `OOD_LLM_API_KEY` present, sending ticket text to a Cloud LLM and changing query mode from deterministic/retrieval-only to LLM-grounded output.

**Why it happens in this project:**
- `Settings.has_llm_credentials` automatically enables non-noop LLM behavior for supported providers.
- Query mode changes from `naive`/retrieval-only behavior to `mix` and may generate answers.
- README states Cloud LLM use is allowed only after privacy approval.

**Consequences:**
- Mock-data tests may pass in one environment and fail in another.
- Privacy assumptions are broken for ticket text if real/anonymized data is accidentally used.
- Evaluation mixes deterministic routing with LLM-generated assessment, making regressions harder to isolate.

**Warning signs:**
- Eval output contains `llm_used: true` without an explicit LLM evaluation suite.
- Local eval results differ when `.env` exists.
- CI secrets include `OOD_LLM_API_KEY` for the default eval job.

**Prevention:**
- Default eval runner must unset/ignore `OOD_LLM_API_KEY`, `OOD_LLM_PROVIDER`, and `OOD_LLM_MODEL` unless `--allow-llm` is explicitly passed.
- Split suites: `eval:local` is mandatory and privacy-safe; `eval:llm` is optional and marked requires privacy approval.
- Record environment mode in every eval report.

**Phase / requirement implications:**
- Address in eval CLI/harness implementation and privacy gate.

**Concrete quality gates:**
- Default evaluation asserts all results have `llm_used: false`.
- Test with an injected fake `OOD_LLM_API_KEY` verifies default eval still runs local-only or fails closed.
- Optional LLM suite cannot run without an explicit flag and a visible privacy warning.

---

## Moderate Pitfalls

### Pitfall 8: Aggregate Scores Hide Failure Modes

**What goes wrong:** A single average score hides that Police routing, Offerte routing, no-answer cases, or red command detection are failing.

**Prevention:** Report metrics by scenario type, source type, system/component, and expected route. Use minimum per-slice thresholds for safety-critical categories.

**Quality gate:** Red-command recall and `Rückfrage` correctness for no-source cases must be separately reported and thresholded.

### Pitfall 9: Duplicate and Near-Duplicate Fixtures Inflate Retrieval Scores

**What goes wrong:** Exact/near duplicates make it easier to hit some relevant source while hiding canonical-source ambiguity.

**Prevention:** Keep duplicates intentionally, but label them as duplicate scenarios. Assert canonical preference where relevant and separately track duplicate-group retrieval behavior.

**Quality gate:** Duplicate report must be reviewed; unexpected duplicate groups fail corpus validation.

### Pitfall 10: Metric Thresholds Are Set Before Baseline Exists

**What goes wrong:** Arbitrary pass/fail thresholds either block development or rubber-stamp weak quality.

**Prevention:** First eval phase should establish a baseline and save a JSON report. Regression gates should compare against baseline plus minimum safety floors.

**Quality gate:** Roadmap should include “baseline-only” before “gated regression” unless existing baseline data is available.

### Pitfall 11: Answer Metrics Are Applied When There Is No Generated Answer

**What goes wrong:** OOD local mode returns `answer=None` by design, so response relevancy/faithfulness metrics are meaningless in the default privacy-safe path.

**Prevention:** In local mode, evaluate retrieved sources and deterministic `analysis`; only run answer/faithfulness metrics for an explicit LLM suite.

**Quality gate:** Eval harness skips answer-quality metrics when `llm_used=false` and reports them as “not applicable”, not zero.

### Pitfall 12: Fixtures Do Not Exercise Existing Safety Behavior

**What goes wrong:** Mock corpus focuses on happy-path runbooks and misses dangerous commands, low confidence, mixed identifiers, and ambiguous tickets.

**Prevention:** Include dedicated negative/safety cases: destructive commands in ticket text, dangerous commands in source excerpts, mixed Police+Offerte identifiers, no matching source, stale/deprecated competing source.

**Quality gate:** Minimum scenario coverage checklist must pass before metrics are trusted.

## Phase-Specific Warnings and Gates

| Phase Topic | Likely Pitfall | Prevention Strategy | Concrete Quality Gate |
|-------------|----------------|---------------------|-----------------------|
| Mock corpus design | Real data leakage; weak metadata | Dedicated mock path, mock frontmatter, fake IDs, privacy scanner | All committed mock/eval files pass PII/secret scan and metadata validator |
| Corpus realism | Easy keyword-only retrieval | Hard negatives, paraphrases, multilingual/noisy tickets, duplicates/stale docs | Scenario coverage report includes exact/paraphrase/noisy/ambiguous/no-answer/safety cases |
| Import/index validation | Warning-only metadata hides poor fixtures | Treat metadata warnings as fatal for mock corpus, though runtime stays warning-only | Eval import fails on `metadata_warnings`, unknown source type, skipped docs unless expected |
| Clean eval runs | Stale storage contaminates metrics | Fresh storage per run or clean reindex, manifest/source reconciliation | No result source outside manifest; no shared `data/storage` dependency |
| Eval schema | Metrics only cover retrieval | Expected outputs include retrieval, routing, IDs, risks, uncertainty | Schema test validates all required expected fields per case |
| Metric implementation | One aggregate quality number | Per-axis and per-slice reports | JSON report separates Retrieval, Routing, IDs, Command Risk, Uncertainty, optional Answer Quality |
| Privacy / LLM mode | `.env` changes eval behavior | Default local-only, explicit `--allow-llm` suite | Default eval asserts `llm_used=false`; optional LLM suite gated by flag |
| Regression gates | Thresholds are arbitrary | Baseline first, then safety floors and regression deltas | Baseline artifact committed for mock eval; CI compares current report to baseline |

## Recommended v1.1 Quality Gates

1. **Mock-data privacy gate:** scan every committed mock Markdown and eval-case file for secrets/PII/real identifiers; fail on missing mock markers.
2. **Metadata gate:** corpus validator fails on any metadata warning for v1.1 mock data, even though normal indexing remains warning-only.
3. **Index reproducibility gate:** eval uses fresh isolated storage and records manifest path, schema version, indexed/skipped counts, duplicate groups, and source paths.
4. **Scenario coverage gate:** eval dataset includes exact, paraphrase, noisy, German/English, no-answer, mixed Police/Offerte, stale/deprecated, duplicate, and command-risk cases.
5. **Retrieval gate:** report Hit@1, Hit@3, MRR, forbidden-source rate, and source-not-in-manifest rate.
6. **Ticket-intelligence gate:** report intent accuracy, route accuracy, identifier exact match/F1, command-risk recall by risk level, and uncertainty correctness.
7. **No-gaming gate:** indexed Markdown may not contain evaluation labels or exact golden-answer phrasing.
8. **LLM/privacy gate:** default eval runs with no Cloud LLM, asserts `llm_used=false`, and marks answer-quality metrics as not applicable.
9. **Baseline gate:** first version stores a baseline report; later changes fail on safety regressions and material retrieval/routing drops.

## Sources

- Project source and tests: `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `README.md`, `src/ood/*.py`, `tests/*.py` — HIGH confidence for project-specific behavior.
- Ragas metrics documentation, “List of available metrics” — documents RAG metrics including context precision/recall, noise sensitivity, response relevancy, faithfulness; useful for metric categories, not a direct implementation mandate. https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/ — MEDIUM confidence.
- LangSmith evaluation concepts — documents offline evaluation workflow with curated datasets, evaluators, experiments, and analysis; useful for baseline/regression framing. https://docs.smith.langchain.com/evaluation/concepts — MEDIUM confidence.

## What Might Be Missing

- LightRAG-specific evaluation best practices were not verified from official LightRAG docs in this pass; v1.1 should validate any LightRAG delete/update semantics before relying on incremental eval storage.
- If the milestone introduces a new eval CLI command or external evaluator library, that phase should perform library-specific research before locking schema and thresholds.
