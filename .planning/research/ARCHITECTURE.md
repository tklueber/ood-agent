# Architecture Research: v1.1 Mockdata-Driven Evaluation

**Project:** OOD Agent  
**Milestone:** v1.1 Evaluations- und Real-Data  
**Researched:** 2026-05-03  
**Scope:** Integration of mock knowledge data, evaluation cases, metric computation, and CLI reporting into the existing Python CLI RAG architecture.  
**Confidence:** HIGH for codebase integration, MEDIUM for exact metric thresholds until realistic mock corpus exists.

> Note: `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, `src/ood/models.py`, `src/ood/rag.py`, `src/ood/cli.py`, and all current `tests/*.py` were reviewed. The requested `src/ood/knowledge.py` file does not exist in the current codebase; knowledge parsing is currently implemented inside `src/ood/rag.py`.

## Current Architecture

The current system is a compact CLI-first Python package with clear separation between stable result models, a service-layer RAG engine, deterministic ticket intelligence, and Typer-based rendering.

```text
User / Tests
  |
  v
Typer CLI (src/ood/cli.py)
  - loads Settings
  - calls RagEngine
  - renders human or JSON output
  |
  v
RagEngine (src/ood/rag.py)
  - discovers Markdown in settings.knowledge_dir
  - strips YAML frontmatter
  - validates metadata as warnings
  - writes manifest and fallback index under settings.storage_dir
  - indexes/query via LightRAG or local fallback
  - calls deterministic ticket intelligence
  |
  v
Stable Dataclass Contracts (src/ood/models.py)
  - IndexResult, UpdateResult, QueryResult
  - SourceHit, ConfidenceScore
  - TicketAnalysis, RoutingDecision, CommandRisk, TicketIdentifier
```

### Current Component Boundaries

| Component | Current Responsibility | v1.1 Integration Implication |
|-----------|------------------------|------------------------------|
| `models.py` | Stable JSON-facing dataclass contracts. | Add evaluation result contracts here, not ad-hoc dicts in CLI. |
| `rag.py` / `RagEngine` | Index, update, reindex, query; owns Markdown parsing and manifest logic. | Reuse as black-box service for evaluation. Avoid embedding evaluation logic into `RagEngine`. |
| `cli.py` | Thin Typer command layer and rendering. | Add `mockdata` and `eval` commands that call dedicated services and emit human/JSON reports. |
| `ticket_intelligence.py` | Deterministic analysis/routing/risk logic. | Evaluation cases should assert analysis fields via `QueryResult.analysis`. No direct CLI parsing. |
| `tests/` | Temporary fixture-driven tests, monkeypatching `RagEngine` and LightRAG. | Continue fixture-first tests with generated temp knowledge/eval files and patched retrieval where needed. |

## Recommended v1.1 Architecture

Add two small service modules and a few stable model types. Keep `RagEngine` unchanged except for optional extraction of Markdown parsing later if code pressure grows. v1.1 should not introduce a plugin system, database, web server, or generalized experiment framework.

```text
Repository fixtures / generated files
  |
  |-- mock knowledge Markdown
  |     knowledge/mock/{tickets,wiki,jira,servicenow}/...
  |
  |-- evaluation cases YAML/JSON
  |     evaluations/v1.1/*.yaml
  |
  v
MockDataService (new: src/ood/mockdata.py)
  - writes clearly marked mock Markdown corpus
  - validates mock-only metadata conventions
  - never overwrites non-mock files by default

EvaluationService (new: src/ood/evaluation.py)
  - loads EvalCase definitions
  - runs RagEngine.query for each case
  - computes retrieval, routing, ID, command-risk metrics
  - returns EvalRunResult dataclass

CLI (modified: src/ood/cli.py)
  - `ood mockdata create|validate` or single `ood mockdata`
  - `ood eval run`
  - human summary + `--json` full result
```

## New vs Modified Components

### New: `src/ood/mockdata.py`

**Purpose:** Own mock corpus generation and mock-safety validation.

Recommended responsibilities:

- Generate deterministic Markdown files into a configured target directory, defaulting to `knowledge/mock/`.
- Use existing Markdown/YAML convention: frontmatter plus body; do not invent a separate source format.
- Include required metadata fields currently enforced by `RagEngine`: `quelle`, `datum`, `status`, `system`, `komponente`, `title`, `type`.
- Add mock-specific metadata fields:
  - `mock: true`
  - `mock_dataset: v1.1`
  - `source_kind: ticket|wiki|jira|servicenow`
  - optional `expected_topics`, `synthetic_id`, `scenario`
- Refuse to overwrite files that are missing `mock: true`, unless an explicit force flag is supplied.
- Return a stable `MockDataResult` dataclass with counts by source kind, target directory, overwritten/skipped files, and warnings.

**Why separate from `RagEngine`:** `RagEngine` should keep indexing/query responsibilities. Mock generation is test/evaluation fixture management, not retrieval behavior.

### New: `src/ood/evaluation.py`

**Purpose:** Run repeatable evaluation cases against the existing query contract.

Recommended responsibilities:

- Load cases from YAML or JSON under `evaluations/`.
- Validate case schema before running queries.
- Run each case via `RagEngine(settings).query(case.query)`.
- Compute metrics from `QueryResult` only:
  - source hit at K from `result.sources[*].path`
  - reciprocal rank from expected source path positions
  - routing accuracy from `result.analysis.routing.route`
  - intent accuracy from `result.analysis.intent`
  - identifier detection from `result.analysis.identifiers`
  - command-risk detection from `result.analysis.command_risks`
  - confidence bucket or minimum confidence checks from `result.confidence.score`
- Return an `EvalRunResult` dataclass containing per-case results and aggregate metrics.

**Why separate from `RagEngine`:** Evaluation is an orchestration and scoring concern. Keeping it outside `RagEngine` avoids coupling production query behavior to test metrics and makes the service reusable in CLI/tests.

### Modified: `src/ood/models.py`

Add stable dataclasses for new CLI JSON contracts:

| Model | Fields | Purpose |
|-------|--------|---------|
| `MockDataResult` | `status`, `target_dir`, `written_files`, `skipped_files`, `counts_by_type`, `warnings`, `message` | Output contract for mock data generation/validation. |
| `EvalCase` | `case_id`, `query`, `expected_sources`, `expected_route`, `expected_intent`, `expected_identifiers`, `expected_command_risks`, `tags` | In-memory validated case. Can be loaded from YAML/JSON. |
| `EvalCaseResult` | `case_id`, `status`, `query_result`, `metrics`, `failures` | Per-case diagnostic output. |
| `EvalMetrics` | `total_cases`, `passed_cases`, `hit_rate_at_1`, `hit_rate_at_3`, `mrr`, `routing_accuracy`, `intent_accuracy`, `identifier_accuracy`, `command_risk_accuracy` | Aggregate scoreboard. |
| `EvalRunResult` | `status`, `case_count`, `metrics`, `case_results`, `message` | CLI-facing evaluation result. |

Keep `to_dict()` methods explicit, matching the existing style. Do not expose LightRAG internals or raw private objects.

### Modified: `src/ood/cli.py`

Add two small command surfaces:

```text
ood mockdata --target-dir knowledge/mock --dataset v1.1 [--force] [--json]
ood eval run --cases-dir evaluations --top-k 3 [--json] [--fail-under 0.8]
```

Recommended CLI behavior:

- Follow existing flags: `--json`, `--verbose`, `--quiet`, `--knowledge-dir`, `--data-dir`, `--storage-dir` where relevant.
- Human `eval run` output should show:
  - overall status
  - case count and pass/fail count
  - metric table: Hit@1, Hit@3, MRR, routing, intent, IDs, command risks
  - failed cases with expected vs actual source/route/intent/risk
- JSON output should be complete and machine-parseable from `EvalRunResult.to_dict()`.
- Do not parse rendered query output. Always consume `QueryResult` directly.

### Modified: Tests

Add tests rather than rewriting current tests:

| Test File | Additions |
|-----------|-----------|
| `tests/test_models.py` | Serialization contracts for `MockDataResult`, `EvalCase`, `EvalMetrics`, `EvalRunResult`. |
| `tests/test_mockdata.py` | Deterministic file generation, required metadata, mock marker, no overwrite of non-mock files. |
| `tests/test_evaluation.py` | Case loading, metric computation, source matching, routing/intent/identifier/risk checks. |
| `tests/test_cli.py` | `mockdata --json`, `eval run --json`, human summary, quiet/verbose behavior. |
| `tests/test_rag.py` | Minimal integration test indexing generated mock Markdown if needed; avoid duplicating mockdata tests. |

## Data Storage Layout

Use files, not a database.

```text
knowledge/
  mock/
    v1.1/
      tickets/
      wiki/
      jira/
      servicenow/

evaluations/
  v1.1/
    retrieval.yaml
    routing.yaml
    command-risk.yaml

data/
  storage/
    ood-manifest.json
    ood-fallback-index.json
  eval-runs/                # optional, only if `--output` is requested
    2026-05-03T...json
```

### Mock Knowledge Markdown Contract

Use canonical Markdown with YAML frontmatter so the existing parser and manifest path remain valid.

```markdown
---
quelle: Mock ServiceNow
datum: 2026-05-03
status: active
system: Bestandssystem
komponente: Policen-Import
title: Mock Incident - Policenimport Timeout
type: servicenow_case
mock: true
mock_dataset: v1.1
source_kind: servicenow
synthetic_id: MOCK-SNOW-001
scenario: policenimport-timeout
---

# Incident: Policenimport Timeout

Klar synthetische Fehlerbeschreibung, Lösungsschritte und Routing-Hinweise...
```

### Evaluation Case Contract

Prefer YAML for hand-written cases because it is readable and reviewable. If the project does not yet have a YAML dependency beyond Pydantic settings, either add `PyYAML` intentionally or start with JSON to avoid dependency churn. Recommendation: use YAML only if `PyYAML` is already present in the lockfile; otherwise JSON is acceptable for v1.1.

```yaml
- case_id: eval-routing-police-001
  query: "Police P-12345: Policenimport läuft in Timeout, was tun?"
  expected_sources:
    any_of:
      - "mock/v1.1/servicenow/policenimport-timeout.md"
      - "mock/v1.1/wiki/policenimport-runbook.md"
    top_k: 3
  expected_route: "weiterleiten Policen"
  expected_intent: "Problem"
  expected_identifiers:
    - kind: police
      value: "P-12345"
  expected_command_risks:
    - command_contains: "restart"
      risk: "orange"
  tags: [retrieval, routing, policen]
```

## Data Flow Changes

### 1. Mock Data Generation Flow

```text
CLI: ood mockdata
  -> load Settings
  -> MockDataService.generate(target_dir, dataset, force)
  -> write Markdown files with required + mock metadata
  -> return MockDataResult
  -> CLI renders result
```

Important integration rule: generated mock data becomes ordinary knowledge input. The existing `ood index`, `ood update`, and `ood reindex` commands should not need special mock branches.

### 2. Import / Index Validation Flow

```text
CLI: ood index/update/reindex --knowledge-dir knowledge/mock/v1.1
  -> existing RagEngine Markdown discovery
  -> existing frontmatter stripping
  -> existing metadata warnings and duplicate detection
  -> manifest records mock metadata as normal metadata
```

For v1.1, validation should be layered:

- `MockDataService.validate()` checks mock safety and dataset conventions.
- `RagEngine` continues checking generic knowledge metadata.
- `ood update --verbose` remains the canonical manifest/import diagnostic.

Do not add mock-only logic to `RagEngine._metadata_warnings()` unless the entire product decides `mock` metadata is globally required. It is not.

### 3. Evaluation Run Flow

```text
CLI: ood eval run
  -> load Settings
  -> EvaluationService.load_cases(cases_dir)
  -> for each EvalCase:
       RagEngine(settings).query(case.query)
       compare QueryResult against expectations
       produce EvalCaseResult
  -> aggregate EvalMetrics
  -> return EvalRunResult
  -> CLI renders summary or JSON
```

This keeps the evaluation harness black-box from the perspective of retrieval. It measures the behavior users see through the same service contract used by the CLI.

## Metric Computation

### Recommended MVP Metrics

| Metric | Compute From | Why It Matters | Complexity |
|--------|--------------|----------------|------------|
| Hit@1 | first `SourceHit.path` in `QueryResult.sources` | Checks whether the best citation is expected. | Low |
| Hit@3 | top 3 source paths | More forgiving retrieval quality signal. | Low |
| MRR | rank of first expected source | Better than binary pass/fail for retrieval ranking. | Low |
| Routing accuracy | `QueryResult.analysis.routing.route` | Validates ticket routing value. | Low |
| Intent accuracy | `QueryResult.analysis.intent` | Validates deterministic ticket classification. | Low |
| Identifier accuracy | `QueryResult.analysis.identifiers` | Validates Police/Offerte extraction. | Medium |
| Command-risk accuracy | `QueryResult.analysis.command_risks` | Validates safety-critical classification. | Medium |
| Confidence threshold pass rate | `QueryResult.confidence.score` | Flags weak retrieval cases. | Low |

Avoid answer-quality scoring in the first v1.1 slice unless LLM usage is explicitly enabled and privacy-approved. In retrieval-only fallback, `answer` is intentionally `None`; scoring generated prose would create false failures.

### Metric Rules

- Normalize paths to POSIX-style relative paths, matching current `SourceHit.path` behavior.
- Allow `expected_sources.any_of` to avoid brittle coupling to one duplicate document.
- Treat an expected source as matched if exact path matches. Do not use fuzzy path matching in v1.1.
- Compute MRR as `1 / rank` of the first matching expected source, or `0.0` if none found.
- Case pass should require all declared expectations to pass. Missing expectation fields are ignored, not counted as failures.
- Aggregate status should be:
  - `passed` when all required cases pass
  - `failed` when any required case fails
  - `no_cases` when no cases are loaded

## Integration Points

| Integration Point | Existing Code | Proposed Change |
|-------------------|---------------|-----------------|
| Stable JSON contracts | `models.py` dataclasses with `to_dict()` | Add evaluation/mock dataclasses. |
| Settings/path overrides | `_load_valid_settings()` in `cli.py` | Reuse for `mockdata` and `eval run`; add only command-specific target/cases options. |
| Knowledge parsing | `RagEngine._parse_markdown_document()` | Reuse indirectly by generating normal Markdown; avoid direct dependency from mockdata if possible. |
| Index validation | `IndexResult`, `UpdateResult`, manifest diagnostics | Use existing index/update commands to validate generated corpus. |
| Query execution | `RagEngine.query()` returns `QueryResult` | EvaluationService calls this directly. |
| Human rendering | `_emit_*_result()` helpers in `cli.py` | Add `_emit_mockdata_result()` and `_emit_eval_result()`. |
| JSON rendering | dataclass `to_dict()` | Keep full machine-readable evaluation payload. |
| Tests | temp dirs, monkeypatch, fake LightRAG | Continue same style; patch `RagEngine.query` in CLI tests. |

## Suggested Build Order

### Step 1: Define Result Contracts

Add `MockDataResult`, `EvalCase`, `EvalCaseResult`, `EvalMetrics`, and `EvalRunResult` to `models.py` with explicit `to_dict()` tests.

**Why first:** CLI and services can evolve against stable contracts, following the existing architecture.

### Step 2: Implement MockDataService

Create deterministic mock Markdown generation and validation in `src/ood/mockdata.py`. Include a small but representative corpus across tickets, wiki, Jira, and ServiceNow.

**Why second:** Evaluation needs a predictable corpus before meaningful cases can be defined.

### Step 3: Add CLI Mockdata Command

Wire `ood mockdata` to `MockDataService`. Test `--json`, human output, and overwrite safety.

**Why third:** Makes corpus generation usable and supports manual indexing validation via existing `ood index/update`.

### Step 4: Define Evaluation Case Loader and Metric Functions

Implement pure functions first:

- `load_eval_cases(path) -> list[EvalCase]`
- `evaluate_case(case, query_result) -> EvalCaseResult`
- `aggregate_metrics(results) -> EvalMetrics`

**Why fourth:** These are deterministic and easy to unit test without LightRAG.

### Step 5: Implement EvaluationService

Use `RagEngine.query()` as the only runtime dependency. Keep per-case failure details verbose enough for roadmap decisions.

**Why fifth:** Service orchestration depends on case models and metric functions.

### Step 6: Add CLI Eval Command

Add `ood eval run` with JSON/human rendering and optional `--fail-under` for CI-like usage.

**Why sixth:** Rendering should come after result shape stabilizes.

### Step 7: End-to-End Fixture Test

Create a temp knowledge directory, generate mock data, index with fallback or fake LightRAG, run a tiny eval suite, assert metrics and JSON contract.

**Why last:** Avoid brittle integration tests before individual contracts are stable.

## Test Approach

### Unit Tests

- Model serialization tests for every new dataclass.
- Mock generator tests assert exact paths, metadata fields, and body content markers.
- Safety tests assert non-mock files are not overwritten.
- Metric tests use handcrafted `QueryResult` instances; no filesystem or LightRAG required.
- Case loader tests validate missing required fields produce clear errors.

### CLI Tests

- Patch services or `RagEngine.query()` similarly to current CLI tests.
- Assert JSON payload keys and human summary lines.
- Assert `--quiet` emits nothing and `--verbose` includes diagnostics.
- Assert `eval run` exits non-zero only if an explicit threshold/fail option requests CI behavior; otherwise it should report failed status with exit code 0 for exploratory local runs.

### Integration Tests

- Use `tmp_path` for `knowledge_dir` and `storage_dir`.
- Generate a tiny mock corpus.
- Run `RagEngine.index_markdown()` in local fallback mode or patched LightRAG.
- Run `EvaluationService.run()` against 1-3 cases.
- Assert at least one retrieval and one routing metric.

## Risks and Mitigations

| Risk | What Goes Wrong | Mitigation |
|------|-----------------|------------|
| Mock data contaminates real knowledge | Synthetic files get mixed into production corpus. | Require `mock: true`, default target `knowledge/mock/v1.1`, validate mock marker, refuse overwrite of non-mock files. |
| Evaluation logic leaks into production query path | `RagEngine` grows flags for expected answers or test modes. | Keep evaluation in `EvaluationService`; call `RagEngine.query()` as black box. |
| Metrics become brittle due to exact top result ordering | Small retrieval changes fail all tests. | Use Hit@3 and `any_of` expected sources; reserve Hit@1 as signal, not only pass criterion. |
| Generated answer scoring fails in retrieval-only mode | Existing privacy-safe mode returns `answer=None`. | Do not require answer quality in v1.1 unless LLM credentials and privacy approval are explicitly active. |
| YAML dependency churn | Adding YAML parser expands dependencies unnecessarily. | Use JSON cases if no YAML parser exists; otherwise use YAML for readability. |
| Overengineered experiment framework | v1.1 becomes a platform instead of a quality loop. | File-based cases, dataclasses, one service, one CLI command. Defer dashboards/tracing. |
| Current knowledge parser is private inside `RagEngine` | Mock validation might duplicate frontmatter parsing. | Accept small duplication for mock-specific validation, or extract a tiny `knowledge.py` later if needed. Do not block v1.1. |

## Explicit Non-Goals for v1.1

- No database for evaluation runs.
- No web UI or dashboard.
- No generic plugin architecture for metrics.
- No automatic ServiceNow/Jira API import.
- No LLM-as-judge scoring until data privacy and reproducibility are addressed.
- No production-data anonymization pipeline in this milestone.

## Roadmap Implications

Recommended phase slicing for v1.1:

1. **Mock Corpus Foundation** — add safe deterministic mock data generation and validation.
2. **Import/Index Validation** — run existing index/update paths against the corpus; surface metadata and manifest diagnostics.
3. **Evaluation Harness** — add case models, loader, metrics, and service orchestration around `RagEngine.query()`.
4. **CLI Reporting** — provide human and JSON reports suitable for manual quality checks and later CI thresholds.

This order minimizes architectural churn: first create reliable data, then prove the existing import/index path, then measure query behavior, then expose reporting.

## Sources

- `.planning/PROJECT.md` — v1.1 active requirements and constraints.
- `.planning/ROADMAP.md` — completed v1 architecture phases and CLI-first direction.
- `.planning/REQUIREMENTS.md` — existing RAG, knowledge, ticket intelligence, and observability requirements.
- `src/ood/models.py` — current stable dataclass JSON contracts.
- `src/ood/rag.py` — current RAG service, Markdown parsing, manifest, fallback, query flow.
- `src/ood/cli.py` — Typer command and rendering patterns.
- `tests/*.py` — current testing style and expected integration contracts.
