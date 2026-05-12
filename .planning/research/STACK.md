# Stack Research: v1.1 Mockdata-Driven Evaluation

**Project:** OOD Agent  
**Milestone:** v1.1 Evaluations- und Real-Data  
**Researched:** 2026-05-03  
**Scope:** Stack additions/changes for mock knowledge generation, RAG evaluation datasets, CLI evaluation runs, and metric reporting.  
**Overall recommendation confidence:** HIGH for stdlib/existing-stack choices; MEDIUM for LightRAG-specific evaluation stability because current retrieval behavior can vary by backend/model availability.

## Recommendation

Do **not** add a dedicated RAG evaluation framework for v1.1. Build the milestone with the existing Python/Typer/RagEngine stack plus small internal modules and Python stdlib data formats:

- **Mock knowledge generation:** deterministic Python generators using `dataclasses`, `random.Random(seed)`, `pathlib`, and explicit Markdown/frontmatter rendering.
- **Evaluation datasets:** JSON files validated by existing `pydantic` or lightweight dataclass loaders; keep expected answers/routes/source IDs separate from generated Markdown.
- **CLI evaluation runs:** add a Typer command such as `ood eval` that reuses `RagEngine.reindex_markdown()` and `RagEngine.query()` against isolated mock directories/storage.
- **Metric reporting:** compute Hit@K, MRR, source recall, route accuracy, intent accuracy, identifier exact-match, command-risk match, and no-result/low-confidence counts with stdlib `statistics`; emit JSON and CSV via stdlib `json`/`csv`.

This keeps v1.1 reproducible, local, privacy-safe, and aligned with the current codebase. The only dependency change I recommend is **none** for runtime. If strict schema diagnostics become painful, use the already-installed `pydantic>=2.7.0`; do not introduce new dependencies just to parse or score a small eval suite.

## Existing Stack Fit

| Existing technology | Keep / change | v1.1 use |
|---|---:|---|
| Python `>=3.10` | Keep | Sufficient for dataclasses, pathlib, json/csv/statistics; current project target is Python 3.10. |
| uv project + lockfile | Keep | No new dependency churn; generated mock data can be produced by package code or tests. |
| Typer `>=0.12.0` | Keep | Add `ood eval` and optionally `ood mockdata generate`; Typer officially supports multi-command CLIs. |
| Rich `>=13.7.0` | Keep | Human-readable eval summaries/tables; JSON remains machine contract. |
| Pydantic / pydantic-settings | Keep | Already present; useful for validating eval case schemas if needed. Do not add another validation library. |
| LightRAG + sentence-transformers + numpy | Keep | Evaluate the actual retrieval path, but isolate storage per run and report backend used. |
| pytest / pytest-cov | Keep | Use `tmp_path` for generated knowledge/eval fixtures and regression tests. |

## Recommended Stack Additions

### 1. Internal module: `ood.mockdata`

**Dependency additions:** none.

Use:

- `dataclasses.dataclass(frozen=True)` for scenario/corpus specs.
- `random.Random(seed)` for deterministic variation.
- `pathlib.Path` for output paths.
- `textwrap.dedent` or small explicit template functions for Markdown bodies.
- Manual frontmatter rendering from `dict[str, str]` because current `RagEngine._split_frontmatter()` only supports simple `key: value` scalar pairs.

Recommended outputs:

```text
knowledge/mock/
  tickets/*.md
  wiki/*.md
  jira/*.md
  servicenow/*.md
evaluation/mock-eval.json
```

Every generated Markdown file should include the already-required metadata plus mock-specific scalar flags:

```yaml
---
quelle: Mock
datum: 2026-05-03
status: active
system: ERP
komponente: Worker
title: Mock worker timeout runbook
type: runbook
mock: true
mock_dataset: v1.1
scenario_id: worker-timeout-001
---
```

**Why:** The current parser strips frontmatter and stores metadata strings in the manifest. A simple scalar convention keeps generation compatible without adding PyYAML or changing the parser in v1.1.

### 2. Internal module: `ood.evaluation`

**Dependency additions:** none.

Use existing models and small new dataclasses/Pydantic models:

- `EvalCase`: `case_id`, `ticket_text`, expected source paths, expected route, expected intent, expected identifiers, expected command risks.
- `EvalCaseResult`: embeds the current `QueryResult.to_dict()` plus metric booleans/scores.
- `EvalRunReport`: aggregate metrics, backend/runtime config, paths, case results.

Use `pydantic.BaseModel` only if schema error messages matter for CLI users. Otherwise dataclasses plus explicit validation is enough and matches current `ood.models` style.

Recommended dataset format: JSON, not YAML.

```json
{
  "schema_version": 1,
  "dataset_id": "mock-v1.1",
  "cases": [
    {
      "case_id": "worker-timeout-001",
      "ticket_text": "Police P-12345 Fehler: Worker Queue timeout nach Import.",
      "expected_sources": ["wiki/worker-timeout.md", "tickets/inc-worker-timeout.md"],
      "expected_route": "weiterleiten Policen",
      "expected_intent": "Problem",
      "expected_identifiers": [{"kind": "police", "value": "P-12345"}],
      "expected_command_risks": [{"risk": "grün", "origin_contains": "worker-timeout"}]
    }
  ]
}
```

**Why:** JSON is already used for CLI output and manifests. Python stdlib `json` supports stable pretty-printed output and decoding; keeping eval fixtures JSON avoids a YAML parser dependency and makes CI diffs straightforward.

### 3. CLI command: `ood eval`

**Dependency additions:** none.

Add a Typer command to `src/ood/cli.py` rather than a separate executable:

```text
ood eval --dataset evaluation/mock-eval.json \
         --knowledge-dir knowledge/mock \
         --storage-dir data/eval/mock-v1.1 \
         --reindex \
         --json \
         --output data/eval/reports/mock-v1.1.json
```

Recommended options:

| Option | Purpose |
|---|---|
| `--dataset PATH` | Eval case JSON. |
| `--knowledge-dir PATH` | Mock knowledge corpus to index. |
| `--storage-dir PATH` | Isolated eval index; should default under `data/eval/`, not normal storage. |
| `--reindex/--no-reindex` | Force clean eval index for reproducibility. Default `--reindex` for mock eval. |
| `--top-k INT` | Scoring cutoff for Hit@K/source recall. Initially score returned list; defer RagEngine top-k configuration unless needed. |
| `--json` | Emit full machine-readable report. |
| `--csv PATH` | Optional case-level metric rows. |
| `--fail-under FLOAT` | Optional CI gate for aggregate score after metrics stabilize. |

**Why:** Current CLI already centralizes settings overrides and JSON output. Keeping eval under Typer avoids another command runner and lets tests use `CliRunner` patterns already present in `tests/test_cli.py`.

### 4. Metric reporting: stdlib JSON/CSV + `statistics`

**Dependency additions:** none.

Recommended metrics for v1.1:

| Metric | Definition | Why |
|---|---|---|
| `hit_at_1`, `hit_at_3`, `hit_at_5` | Any expected source appears in first K source paths. | Simple retrieval health signal. |
| `mrr` | Reciprocal rank of first expected source, averaged. | Rewards correct ordering, not just presence. |
| `source_recall_at_k` | Expected sources found in first K / expected sources. | Handles multi-source cases. |
| `route_accuracy` | `analysis.routing.route == expected_route`. | Validates ticket-intelligence routing. |
| `intent_accuracy` | `analysis.intent == expected_intent`. | Validates deterministic intent classifier. |
| `identifier_exact_match` | Expected IDs are present with same kind/value. | Validates police/offerte extraction. |
| `command_risk_match` | Expected risk labels found. | Validates safety classification. |
| `no_result_rate` | Cases with `status == "no_results"` or empty sources. | Detects index/retrieval regressions. |
| `low_confidence_rate` | Cases below chosen threshold, e.g. `<0.5`. | Tracks usefulness without requiring LLM. |

Use `statistics.fmean()` for aggregate percentages/means and `statistics.median()` for score/latency medians if runtime is measured. Emit:

- full run JSON for machines and regression snapshots;
- compact CSV for spreadsheet-friendly case rows;
- Rich table for humans.

Python stdlib docs confirm `json` supports serialization/deserialization and pretty printing; `csv.DictWriter` supports dictionary-based output; `statistics` provides mean/median-type functions for numeric data.

## Avoided Dependencies

| Avoid | Why not for v1.1 | Reconsider when |
|---|---|---|
| Ragas / DeepEval / TruLens / Phoenix eval stack | Too heavy for current deterministic CLI evaluation; often assumes LLM-as-judge, tracing, hosted dashboards, or broader app instrumentation. v1.1 needs mock regression metrics, not benchmark platform complexity. | After real/anonymized data and LLM-answer quality eval are approved. |
| Faker | Generated incidents need domain-specific controlled expectations, not random realistic-looking text. `random.Random(seed)` plus templates is more reproducible and privacy-safe. | If large-volume synthetic variation becomes valuable after core scenarios are stable. |
| PyYAML / ruamel.yaml | Current frontmatter parser handles simple scalar keys and Markdown remains canonical. YAML dependencies add parser behavior surface area without clear v1.1 value. | If nested/list frontmatter becomes a hard requirement. |
| pandas | CSV/JSON metric tables are small and can be produced with stdlib. Pandas would add dependency weight for little value. | If reports become exploratory notebooks or need joins across many historical runs. |
| scikit-learn metrics | Retrieval and classification metrics are simple enough to implement transparently. | If evaluation expands to statistical model comparison or complex multilabel metrics. |
| pytest plugins for golden snapshots | Existing pytest is sufficient. Plain JSON expected fixtures are easier to review. | If snapshot volume becomes hard to maintain manually. |

## Integration Points

### `RagEngine`

- Reuse `RagEngine.reindex_markdown()` for clean eval setup.
- Reuse `RagEngine.query(ticket_text)` and score only the public `QueryResult` contract; do not inspect LightRAG internals.
- Add no retrieval-engine coupling in `ood.evaluation`; this keeps fallback retrieval and LightRAG retrieval comparable through the same public output shape.
- For reproducibility, the eval runner should record:
  - `knowledge_dir`, `storage_dir`, `dataset_path`;
  - whether fallback or LightRAG path was used;
  - `llm_used` counts;
  - package version and dataset schema version.

### CLI

- Follow current JSON contract style: `--json` emits one JSON object, not mixed Rich output.
- Human output should be compact: aggregate table plus failed cases with expected vs actual.
- `--quiet` should suppress non-essential output but still write report files if requested.
- `--verbose` should include manifest/index diagnostics and per-case misses.

### Config and paths

- Prefer explicit `--knowledge-dir` and `--storage-dir` overrides for eval runs.
- Store generated runtime artifacts under `data/eval/` so they stay outside Git, matching existing project constraints.
- Store committed mock knowledge only if clearly namespaced and marked, e.g. `knowledge/mock/` or `tests/fixtures/knowledge/mock/`.
- Store eval datasets under a source-controlled, non-runtime directory such as `evaluation/` or `tests/fixtures/evaluation/`.

### Privacy and mock-data separation

- Require `mock: true` and `mock_dataset: ...` in all generated mock knowledge frontmatter.
- Add a validation pass before `ood eval` that fails if a mock dataset references files missing `mock: true` when `--require-mock` is enabled.
- Do not use `.env` or cloud LLM credentials in default eval. The default should be retrieval-only/fallback-safe unless the user explicitly opts in.
- Report `llm_used` at aggregate and case level to make accidental cloud use visible.

## Version and Dependency Risk

| Risk | Level | Notes / mitigation |
|---|---:|---|
| Python docs fetched are 3.14 while project targets 3.10 | LOW | Recommended stdlib APIs (`json`, `csv.DictWriter`, `statistics.mean/median/fmean`) are available in Python 3.10. Avoid newer APIs such as `statistics.kde` in project code. |
| LightRAG retrieval behavior may vary by backend/index state | MEDIUM | Use isolated storage and `--reindex` by default. Store backend metadata and separate fallback vs LightRAG baselines. |
| Local embedding model download/runtime changes | MEDIUM | Eval should tolerate cold-start costs and record runtime. For CI, prefer fallback or mark LightRAG eval as slower/integration-level. |
| Current fallback retrieval is lexical and simplistic | MEDIUM | Useful for deterministic tests, but not representative of LightRAG quality. Report backend and do not mix baselines. |
| Frontmatter parser is intentionally simple | LOW | Keep generated metadata scalar-only. Do not add nested YAML in mock data. |
| Metric definitions can drift | MEDIUM | Put `schema_version` in eval datasets and report files; test metric functions with hand-built `QueryResult` fixtures. |
| Accidental real-ticket indexing in eval | HIGH if unchecked | Add `--require-mock` default for mock eval and fail if indexed docs lack `mock: true`/`quelle: Mock`. |

## Installation / Dependency Changes

No new packages are recommended.

```bash
# No runtime dependency additions for v1.1 evaluation.

# Existing dev commands remain sufficient:
uv run pytest
uv run ood --help
```

If later phases require LLM-as-judge evaluation, tracing, or dashboards, perform a separate comparison research task before adding Ragas/DeepEval/TruLens/Phoenix/Langfuse dependencies.

## Sources

- Existing project context: `.planning/PROJECT.md`, `.planning/REQUIREMENTS.md`, `pyproject.toml`, `src/ood/*.py`, `tests/*.py` (HIGH confidence for integration decisions).
- Python stdlib `json` documentation: https://docs.python.org/3/library/json.html (HIGH confidence; official docs).
- Python stdlib `csv` documentation: https://docs.python.org/3/library/csv.html (HIGH confidence; official docs).
- Python stdlib `statistics` documentation: https://docs.python.org/3/library/statistics.html (HIGH confidence; official docs; avoid APIs newer than Python 3.10).
- Typer commands documentation: https://typer.tiangolo.com/tutorial/commands/ (HIGH confidence for adding `ood eval` as a Typer command).
- pytest `tmp_path` documentation: https://docs.pytest.org/en/stable/how-to/tmp_path.html (HIGH confidence for fixture-based mock/eval tests).
