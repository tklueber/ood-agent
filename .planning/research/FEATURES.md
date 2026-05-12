# Feature Landscape: v1.1 Mockdata-Driven Evaluation

**Project:** OOD Agent  
**Milestone:** v1.1 Evaluations- und Real-Data  
**Domain:** Local-first Python CLI RAG assistant for German ServiceNow ticket triage  
**Researched:** 2026-05-03  
**Overall confidence:** HIGH for local fixture/eval workflow, MEDIUM for external eval-tool choices

## Scope Boundary

This research focuses only on new v1.1 capabilities. The existing implementation already provides:

- CLI commands: `index`, `reindex`, `update`, `query`
- Markdown knowledge ingestion with YAML frontmatter
- Manifest-based incremental updates, metadata warnings, duplicate reports, stale path diagnostics
- Query JSON/human output with sources, confidence, deterministic ticket intent/routing/ID/command-risk analysis
- Privacy-safe retrieval-only behavior without Cloud LLM credentials

v1.1 should therefore add **mock corpus breadth, import/index validation, expected-answer fixtures, and reproducible evaluation reporting** without changing the core CLI contract unless a dedicated `eval` command is chosen.

## Feature Categories

### 1. Mock Knowledge Corpus

Goal: Provide enough realistic, clearly fake German operational knowledge to exercise retrieval, duplicate detection, metadata diagnostics, routing, and command-risk classification.

| Feature | User-Facing Behavior | Complexity | Dependencies on Existing Implementation | Notes |
|---|---|---:|---|---|
| Curated mock Markdown corpus | User can index a ready-made corpus and query realistic ServiceNow/Jira/Wiki cases. | Medium | Existing recursive Markdown discovery and frontmatter parsing | Put under a sample directory such as `examples/mock_knowledge/` or `knowledge/mock/`; avoid default production-looking names unless explicit. |
| Source-type coverage | Corpus includes Wiki articles, ServiceNow incidents/cases, Jira bugs, runbooks, and Markdown notes. | Medium | Existing `type`, `quelle`, `system`, `komponente` metadata fields | Use distinct folders (`wiki/`, `servicenow/`, `jira/`, `runbooks/`, `notes/`) so expected sources are stable. |
| German ticket/domain scenarios | Queries use German support language, Police/Offerte terminology, and operational error wording. | Medium | Existing German intent/routing strings and ID regexes | Preserve domain terms: `Police`, `Policennummer`, `Offerte`, `Offertennummer`, `weiterleiten Policen`, `weiterleiten Offerten`, `Rückfrage`. |
| Explicit mock marking in every document | Every mock document is visibly marked as fake in frontmatter and body. | Low | Existing metadata warning system, but no custom `mock` validation yet | Add fields like `mock: true`, `data_classification: mock`, `contains_real_customer_data: false`, plus body warning: `⚠️ MOCKDATEN – keine echten Kunden-/Ticketdaten`. |
| Evaluation-oriented edge cases | Corpus intentionally includes duplicates, deprecated docs, draft docs, stale scenarios, low-signal notes, conflicting-ish old guidance. | Medium | Existing duplicate/status/manifest diagnostics | Include exact and near duplicates because current code already reports them without blocking indexing. |
| Safe command-risk examples | Some docs contain read-only, reversible, state-changing, and destructive command examples. | Low | Existing command-risk patterns scan ticket text and source excerpts | Use fake systems and safe placeholders; never include real hosts, credentials, or production namespaces. |

### 2. Importable Sample Data and Validation

Goal: Make the mock corpus easy to load into a clean local runtime and verify that indexing/update behavior works end-to-end.

| Feature | User-Facing Behavior | Complexity | Dependencies | Notes |
|---|---|---:|---|---|
| Sample-data import/copy workflow | User can populate a local knowledge directory from versioned mock fixtures. | Medium | Existing CLI path overrides support `--knowledge-dir`, `--data-dir`, `--storage-dir` | Prefer a new `ood sample-data install` or documented `cp -R examples/mock_knowledge knowledge/mock`. For v1.1, a Python helper/module is enough if CLI scope should stay small. |
| Import is idempotent | Re-running import does not duplicate documents unexpectedly. | Medium | Manifest hash diff expects stable paths/content | Stable file names and deterministic generated IDs. If installer exists, it should refuse overwrite unless `--force`. |
| Mock-only safety guard | User can verify a directory contains only mock docs before indexing/eval. | Medium | Existing parser can read metadata but does not enforce `mock` fields | Add validation routine/report: fail eval if any fixture lacks `mock: true` or has suspicious real-data markers. |
| Index smoke validation | User can run index/reindex/update against mock data and see expected counts/warnings. | Low | Existing `index`, `reindex`, `update --json` output | Tests should assert document counts, skipped docs, metadata warnings, duplicate groups, no-change behavior, and stale path diagnostics. |
| Fixture directory contract | README documents exact commands and folder semantics. | Low | Existing README path override docs | User should never need real ServiceNow/Jira API credentials for v1.1. |

### 3. Evaluation Dataset and Expected-Answer Fixtures

Goal: Define what “good” looks like for OOD Agent before tuning retrieval or prompts.

| Feature | User-Facing Behavior | Complexity | Dependencies | Notes |
|---|---|---:|---|---|
| Versioned eval cases | A fixture file lists ticket inputs and expected outputs. | Medium | Existing `RagEngine.query(...).to_dict()` contract | Use JSONL or YAML. JSONL is robust for batch runs; YAML is easier for humans. Keep one test case per ticket. |
| Expected source hits | Each case declares required/forbidden source paths and optional rank expectations. | Medium | Existing `sources[].path`, `sources[].score` | Evaluate retrieval with hit@k, source presence, forbidden/deprecated source avoidance. Avoid requiring exact scores because scoring can shift. |
| Expected routing | Each case declares expected route: `selbst lösen`, `weiterleiten Policen`, `weiterleiten Offerten`, `Rückfrage`. | Low | Existing deterministic routing | This can be exact-match tested without LLM-as-judge. |
| Expected intent | Each case declares `Problem`, `Frage`, `Request`, or `Unklar`. | Low | Existing deterministic intent classifier | Include German phrasing that stresses current marker order, e.g. questions containing `Fehler` currently classify as `Frage` if `?`/`Wie` appears. |
| Expected IDs | Cases specify expected police/offerte identifiers and ambiguous mixed-context behavior. | Low | Existing ID regexes | Include Police-only, Offerte-only, mixed Police+Offerte, and bare number should be ignored. |
| Expected command risks | Cases specify expected risk labels from ticket text and retrieved source excerpts. | Medium | Existing source-origin risk scanning | Include `kubectl get` (grün), `restart service` (orange), `rm -rf`/`sudo`/`kubectl delete` (rot). |
| Expected answer criteria | Cases define required facts/solution steps rather than exact generated prose. | Medium | Existing `answer` may be `None` without Cloud LLM; `analysis.solution_steps` only populated with LLM answer | In retrieval-only mode, evaluate answer criteria as “not applicable” or evaluate source coverage instead. Do not require generated German prose without LLM credentials. |
| Dataset split metadata | Cases tagged as smoke, regression, edge, routing, command-risk, duplicate, deprecated, no-results. | Low | New eval runner/filtering | Allows fast CI smoke set and fuller local regression suite. |

Recommended eval-case schema:

```yaml
- id: POL-LOGIN-001
  ticket: "Police P-12345: Fehler beim Login nach Passwortwechsel"
  tags: [smoke, retrieval, routing, german, police]
  expected:
    required_sources: ["servicenow/incidents/pol-login-passwordwechsel.md"]
    acceptable_sources:
      - "wiki/login/passwortwechsel.md"
      - "runbooks/login-cache-reset.md"
    forbidden_sources: ["jira/offerten-ui-timeout.md"]
    intent: "Problem"
    route: "weiterleiten Policen"
    identifiers:
      - kind: "police"
        value: "P-12345"
    min_confidence: 0.5
    required_answer_facts:
      - "Passwortwechsel/Login-Cache prüfen"
      - "Quelle nennen"
    command_risks: []
```

### 4. Evaluation Runner and Metrics

Goal: Run all eval cases reproducibly and produce a machine-readable report plus a concise human summary.

| Feature | User-Facing Behavior | Complexity | Dependencies | Notes |
|---|---|---:|---|---|
| Local eval runner | User runs a command/script that indexes mock data, queries eval tickets, scores results, and writes a report. | High | Existing CLI/service APIs; temp dirs recommended | Best v1.1 shape: `uv run python -m ood.eval ...` or `uv run ood eval ...` if adding CLI is acceptable. |
| Retrieval metrics | Report includes hit@1/hit@3/hit@5, MRR, required-source recall, forbidden-source violations. | Medium | Existing source paths are stable | RAG guidance consistently separates retrieval evaluation from generation evaluation. |
| Ticket-intelligence metrics | Report includes exact-match accuracy for intent, route, ID extraction, and command-risk labels. | Medium | Existing deterministic analysis output | These are stronger than LLM-based grading for v1.1 because expected labels are explicit. |
| Confidence calibration checks | Report flags cases where confidence is high with wrong source or low despite required source hit. | Medium | Existing confidence score | Start with thresholds and warnings, not pass/fail gates, because confidence heuristic is simplistic. |
| Import/index metrics | Report includes indexed count, skipped count, metadata warnings, duplicate groups, update diff behavior. | Medium | Existing `IndexResult`/`UpdateResult` | Treat missing mock marking as fail; metadata warning count can be expected in edge fixtures. |
| JSON report artifact | `data/evals/` or configurable output contains run metadata, case results, metrics, failures. | Medium | Existing `data/` is gitignored | Keep generated reports out of git by default; allow committed golden summaries only if sanitized. |
| Markdown summary artifact | Human-readable table of pass/fail cases and top failures. | Low | New eval runner | Useful for roadmap and manual review. |
| CI-friendly exit codes | Eval exits non-zero when required gates fail. | Medium | Current CLI already uses exit code 1 for missing index | Start with smoke suite gates; keep full suite as informational until stable. |

### 5. Documentation and Developer Workflow

Goal: Make v1.1 usable by a developer/operator without reading internals.

| Feature | User-Facing Behavior | Complexity | Dependencies | Notes |
|---|---|---:|---|---|
| README evaluation section | User sees exactly how to install mock data, index, query sample tickets, run evals, and inspect reports. | Low | Existing README structure | Include privacy statement: mock only, no Cloud LLM needed. |
| Example queries | User can copy 5–10 realistic German tickets and see expected routing/sources. | Low | Existing `ood query` | Cover Police, Offerte, Rückfrage, command-risk, no-results. |
| Fixture authoring guide | Maintainer knows how to add a new mock doc and eval case. | Medium | New fixture conventions | Include frontmatter template and eval-case checklist. |

## Table Stakes

Features users/maintainers will expect. Missing = v1.1 does not fulfill its milestone goal.

| Feature | Why Expected | Complexity | Notes |
|---|---|---:|---|
| Extensive mock corpus across Wiki, ServiceNow, Jira, runbooks, notes | The milestone explicitly requires realistic Prüfung before real/anonymized data. | Medium | Aim for breadth: 30–60 docs minimum for useful retrieval behavior; include 10–20 high-value scenarios first if time constrained. |
| Explicit mock-data marking | Privacy/security constraint demands clear separation from real data. | Low | Must be visible in frontmatter and body. Treat missing mock marker as eval failure. |
| Import/index validation | Existing CLI is only trustworthy if sample data exercises reindex/update/no-change/stale paths. | Medium | Use temporary directories in automated tests to avoid polluting local `data/`. |
| Evaluation cases with expected sources | Retrieval quality cannot be measured from generated answer alone. | Medium | Required-source presence should be the primary retrieval score. |
| Evaluation cases with expected routing/intent/IDs/risks | Ticket intelligence is deterministic and should be regression-tested exactly. | Medium | These can be pytest-level assertions and CI gates. |
| Metrics report | Roadmap needs measurable baseline before improvement work. | Medium | Include aggregate metrics and per-case failures. |
| Local-first/offline default | Privacy behavior and current implementation support no-cloud mode. | Low | No eval should require Cloud LLM by default. |
| German domain preservation | The product value is operational German ticket triage. | Medium | Use German inputs and Swiss/German insurance domain labels consistently. |

## Differentiators

Not strictly required by generic RAG evals, but valuable for OOD Agent.

| Feature | Value Proposition | Complexity | Notes |
|---|---|---:|---|
| Mock-data safety validator | Prevents accidental mixing of real ServiceNow/Jira exports into committed fixtures. | Medium | Scan metadata and text for missing `mock: true`, emails, real-looking hostnames, secrets, IBAN-like/customer-like patterns. |
| Scenario matrix coverage report | Shows which operational categories are covered and which are missing. | Medium | Matrix by source type × system × component × route × risk. Helps curate corpus rather than just adding random docs. |
| Golden-source debugging output | For failed cases, show retrieved paths vs required/acceptable/forbidden paths. | Low | Speeds tuning of corpus wording and retrieval behavior. |
| Separate retrieval vs ticket-intelligence scores | Pinpoints whether failure is retrieval, routing, ID extraction, or risk classification. | Medium | Aligns with Promptfoo and LangSmith guidance to evaluate critical components separately. |
| Regression baseline comparison | Compares current eval run to previous JSON report. | Medium | Useful once retrieval settings or corpus shape changes. Defer if v1.1 scope tight. |
| Edge-case packs | Purpose-built cases for duplicates, deprecated docs, mixed Police+Offerte, ambiguous intent, command-risk from source. | Medium | More useful than only happy-path mock docs. |
| Optional LLM-as-judge suite | If privacy-approved credentials exist, evaluate answer helpfulness/faithfulness. | High | Optional only; deterministic suite remains canonical for v1.1. |

## Anti-Features

Features to explicitly not build in v1.1.

| Anti-Feature | Why Avoid | What to Do Instead |
|---|---|---|
| Real ServiceNow/Jira API import | Out of scope; privacy and credentials would dominate the milestone. | Use manually curated mock Markdown fixtures. |
| Committing real/anonymized production tickets | Even anonymized data can leak patterns or identifiers; milestone asks clearly marked mock data. | Use synthetic but realistic German tickets marked as mock. |
| Exact answer string matching for generated prose | Retrieval-only mode has `answer=None`; LLM wording is nondeterministic. | Evaluate required facts, source hits, and deterministic analysis labels. |
| Mandatory Cloud LLM judge | Violates local-first/privacy-default behavior and makes CI flaky/costly. | Keep optional LLM-as-judge behind explicit env flag. |
| Overfitting the corpus to tiny eval queries | Leads to inflated metrics and poor real-world transfer. | Use varied German phrasings, synonyms, noisy ticket text, and distractors. |
| Expanding into Web UI/Teams/automation | Explicitly out of scope and distracts from data/eval foundation. | Document CLI-only workflows. |
| Tool execution for commands | Existing safety model classifies only; executing commands is out of scope. | Continue to classify and report risk labels. |
| Requiring exact relevance scores | Scores vary with retrieval backend/version and fallback mode. | Use rank/source presence thresholds, not exact score equality. |

## Requirement Candidates for v1.1

Suggested requirements to add to `.planning/REQUIREMENTS.md` or roadmap phases.

| ID | Candidate Requirement | Type | Acceptance Signal |
|---|---|---|---|
| MOCK-01 | Repository includes an extensive mock Markdown knowledge corpus covering Wiki, ServiceNow, Jira, runbooks, and notes. | Table stakes | `ood index --knowledge-dir <mock>` indexes expected non-zero count. |
| MOCK-02 | Every committed mock document is explicitly marked with `mock: true` and visible mock warning text. | Table stakes / safety | Mock validator fails any unmarked document. |
| MOCK-03 | Mock corpus preserves German ticket/domain context including Police, Offerte, routing, and operational command examples. | Table stakes | Coverage report shows cases for Policen, Offerten, Rückfrage, selbst lösen, and all command-risk colors used by current classifier where feasible. |
| MOCK-04 | Sample-data import workflow can populate a local knowledge directory idempotently. | Table stakes | Re-running import produces no duplicate paths and clear overwrite behavior. |
| EVAL-01 | Versioned eval dataset defines ticket inputs, expected sources, intent, route, identifiers, command risks, and tags. | Table stakes | Fixture parser validates all cases. |
| EVAL-02 | Eval runner executes OOD queries over the mock corpus and emits JSON + Markdown reports. | Table stakes | Report includes per-case actual vs expected and aggregate metrics. |
| EVAL-03 | Retrieval metrics include hit@k, MRR, required-source recall, and forbidden-source violations. | Table stakes | Failing required source impacts pass/fail score. |
| EVAL-04 | Ticket-intelligence metrics include exact-match accuracy for intent, routing, ID extraction, and command-risk labels. | Table stakes | Deterministic labels are CI-testable. |
| EVAL-05 | Eval workflow has CI-friendly smoke mode and full local mode. | Differentiator | `--suite smoke` finishes fast; full suite can be run manually. |
| EVAL-06 | Eval never sends ticket text to Cloud LLM unless an explicit opt-in flag/env is provided. | Table stakes / privacy | Tests assert default eval uses retrieval-only/local behavior. |
| EVAL-07 | Evaluation reports include scenario coverage and failure diagnosis by component. | Differentiator | Summary separates retrieval failures from routing/ID/risk failures. |

## Feature Dependencies

```text
Mock corpus convention → Mock safety validator → Import/index validation
Mock corpus convention → Eval dataset expected source paths → Retrieval metrics
Eval dataset expected labels → Ticket-intelligence metrics → CI-friendly smoke gate
Existing RagEngine.query JSON contract → Eval runner → JSON/Markdown eval reports
Existing metadata/manifest diagnostics → Import/index metrics → Corpus quality gates
Optional Cloud LLM credentials → Optional LLM-as-judge answer metrics
```

## Recommended MVP Slice for v1.1

Prioritize in this order:

1. **Mock corpus contract and corpus seed**
   - 30–60 Markdown docs if feasible; otherwise 15–25 dense docs across all required source types.
   - Every doc has required existing frontmatter plus `mock: true` and visible mock warning.

2. **Evaluation dataset fixtures**
   - 15–30 ticket cases across smoke/regression/edge tags.
   - Each case includes expected required sources and deterministic analysis expectations.

3. **Local eval runner/report**
   - Runs in temp data/storage directories.
   - Emits JSON and Markdown report.
   - Scores retrieval and deterministic ticket intelligence separately.

4. **Import/index validation tests**
   - Assert mock corpus indexes, update no-change works, expected duplicates/warnings are reported.

5. **README workflow**
   - Copy-paste commands for installing/indexing/querying/evaluating mock data.

Defer:

- LLM-as-judge answer quality: useful but optional and privacy/cost dependent.
- LangSmith/DeepEval/Promptfoo integration: not needed until local bespoke metrics stabilize.
- Synthetic data generator: high risk of low-quality/overfit fixtures; hand-curated seed data is better first.

## User-Facing Behavior Recommendations

### Minimal CLI/Script UX

If adding a CLI command is acceptable:

```bash
uv run ood sample-data install --target knowledge/mock
uv run ood reindex --knowledge-dir knowledge/mock --storage-dir data/mock-storage --json
uv run ood eval --knowledge-dir knowledge/mock --storage-dir data/mock-storage --suite smoke --json
```

If avoiding CLI expansion:

```bash
cp -R examples/mock_knowledge knowledge/mock
uv run ood reindex --knowledge-dir knowledge/mock --storage-dir data/mock-storage --json
uv run python -m ood.eval --knowledge-dir knowledge/mock --storage-dir data/mock-storage --cases evals/mock_cases.yaml
```

Recommended output summary:

```text
OOD Eval: mock-v1.1 smoke
Cases: 12 passed / 14 total
Retrieval: hit@1=0.71 hit@3=0.93 mrr=0.82 required_source_recall=0.93
Ticket Intelligence: intent=1.00 routing=0.93 identifiers=1.00 command_risk=0.86
Failures:
- OFF-UI-003 retrieval: missing required source jira/offerten-ui-timeout.md; got wiki/login/cache.md
- CMD-RISK-002 command_risk: expected orange restart service, got gelb restart
Report: data/evals/mock-v1.1-20260503T120000Z.json
```

## Sources and Verification

| Source | Confidence | Relevant Finding |
|---|---|---|
| Current repo files: `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `README.md`, `src/ood/*.py`, `tests/*.py` | HIGH | v1.1 active requirements, existing CLI/RAG/ticket-intelligence contracts, privacy constraints, JSON fields, manifest diagnostics. |
| Ragas official docs, “List of available metrics” | HIGH | RAG evaluation commonly uses context precision/recall, response relevancy, faithfulness, factual correctness, semantic/string metrics. |
| Promptfoo official docs, “Evaluating RAG pipelines” updated 2026-05-03 | HIGH | Evaluate retrieval and generation separately; use factuality, answer relevance, context adherence/recall/relevance, custom document-citation assertions. |
| LangSmith official docs, “Evaluation concepts” | HIGH | Start with manually curated examples; offline eval datasets have inputs/reference outputs/metadata; evaluate critical components separately; use code evaluators for deterministic structure/classification. |
| DeepEval official docs, quickstart | MEDIUM | Local evals can use test cases, expected outputs, metrics, local JSON result folders; LLM-as-judge needs model credentials. Useful later, not required for v1.1. |
| OpenAI Cookbook, “Getting Started with OpenAI Evals” dated 2024-03-21 | MEDIUM | Evals are datasets plus graders; code-based checks and model-graded checks both exist; evals help CI/regression. Note source itself recommends newer hosted evals, so use for concepts only. |

## Confidence Assessment

| Area | Confidence | Reason |
|---|---|---|
| Mock corpus requirements | HIGH | Directly specified by project requirements and current Markdown/frontmatter implementation. |
| Deterministic ticket-intelligence evaluation | HIGH | Existing models/tests expose exact stable labels and JSON contract. |
| Retrieval metrics | HIGH | Confirmed by RAG eval docs and straightforward over existing source paths. |
| Answer-quality evaluation | MEDIUM | Standard ecosystem supports it, but current default has `answer=None` without Cloud LLM, so v1.1 should not gate on it. |
| External framework adoption | MEDIUM | Ragas/DeepEval/Promptfoo/LangSmith are credible, but OOD’s local-first CLI can meet v1.1 needs with lightweight custom metrics first. |
