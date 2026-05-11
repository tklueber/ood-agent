# OOD Agent

OOD Agent is a local-first RAG assistant for ServiceNow ticket triage. It will search curated Markdown knowledge sources and return concrete solution suggestions with source references and routing guidance.

## Setup

Install dependencies with uv:

```bash
uv sync
```

Run the scaffold and configuration tests:

```bash
uv run pytest -q
```

## Core RAG usage

Build the initial local knowledge index from Markdown files under `knowledge/`:

```bash
uv run ood index
```

Rebuild the index from scratch when source content or retrieval settings change:

```bash
uv run ood reindex
```

Query the indexed knowledge base in human-readable mode:

```bash
uv run ood query "Wie löse ich den Fehler?"
```

Use JSON output for automation:

```bash
uv run ood query "Wie löse ich den Fehler?" --json
```

Check configured paths and local index counts:

```bash
uv run ood status
```

## Knowledge Management

Markdown remains the canonical knowledge format. For best diagnostics, each knowledge file should include YAML frontmatter with these required fields: `quelle`, `datum`, `status`, `system`, `komponente`, `title`, and `type`. Recognized `status` values are `active`, `deprecated`, and `draft`.

Run hash-based incremental indexing with:

```bash
uv run ood update
```

`uv run ood update` compares current Markdown files with the runtime manifest and indexes only new or changed files. If no manifest exists yet, the command bootstraps by indexing all non-empty Markdown files and creating the manifest.

Use JSON diagnostics for automation:

```bash
uv run ood update --json
```

The JSON payload includes manifest diff details, metadata warnings, duplicate groups, stale/deleted paths, indexed paths, skipped paths, and counts. Metadata warnings and duplicate findings are reporting-only and do not block indexing. Deleted files are reported as stale/deleted entries; use `uv run ood reindex` for a clean rebuild/cleanup.

The runtime manifest is stored under the configured `storage_dir` as `ood-manifest.json`, outside git alongside retrieval artifacts.

Audit the external OOD-KB corpus for source-data quality before trusting metadata/graph boosts:

```bash
uv run ood quality-audit \
  --corpus-dir /Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/articles \
  --expected-documents 438 \
  --report-path data/reports/ood-kb-quality.json \
  --json
```

Reports are local JSON files only when `--report-path` is provided. Keep generated reports under `data/` so they remain outside git. See `docs/ood-kb-source-quality.md` for normalized metadata, synonym, Wikilink, command-risk, freshness, owner, and source-attribution guidance.

Local-first retrieval is the default. When Cloud LLM usage is not explicitly approved, OOD stores and queries a local sentence-transformer vector artifact named `ood-local-vector-index.json` under `storage_dir`. This path keeps Markdown body text and embeddings local while preserving the normal `SourceHit` query contract.

Query results are capped to the top 5 source documents to keep operator output focused. Each source includes an excerpt, path, and score. OOD does not print or send the complete source document by default when a chunk matches; operators can open the cited Markdown path if they need full context. This keeps responses concise and avoids accidentally over-sharing source content.

## Mock Corpus

v1.1 starts with synthetic mock data only. Generate the default privacy-safe corpus under `knowledge/mock/v1` with:

```bash
uv run ood mock-init
```

Validate the mock corpus before indexing or sharing it:

```bash
uv run ood mock-validate
```

Automation can use JSON for both steps:

```bash
uv run ood mock-init --json
uv run ood mock-validate --json
```

Use explicit path overrides when creating or checking a copy outside the default location:

```bash
uv run ood mock-init --target-dir /path/to/knowledge/mock/v1 --dataset mock-v1
uv run ood mock-validate --corpus-dir /path/to/knowledge/mock/v1
```

Every mock Markdown file must visibly declare the boundary with `mock: true`, `dataset`, a `synthetic_id` prefixed with `MOCK-`, and a first body warning containing `MOCK DATA` and `SYNTHETIC`. Mock documents also keep the normal knowledge metadata (`quelle`, `datum`, `status`, `system`, `komponente`, `title`, `type`) so they remain importable as Markdown knowledge.

Never put golden answers, expected sources, forbidden sources, or evaluation labels into indexed Markdown. Those belong in future evaluation JSON fixtures, not the knowledge corpus. The validator flags missing mock markers, suspicious PII/secret-like strings, production-looking ServiceNow/Jira/ticket IDs, and golden-answer leakage.

Phase 6 can index the generated mock corpus with the existing local workflow:

```bash
uv run ood index --knowledge-dir knowledge/mock/v1
```

For a complete local mock import and index validation cycle, use the same commands as ordinary Markdown knowledge with explicit mock paths:

```bash
uv run ood mock-init
uv run ood mock-validate
uv run ood index --knowledge-dir knowledge/mock/v1 --storage-dir data/mock-storage --json
uv run ood reindex --knowledge-dir knowledge/mock/v1 --storage-dir data/mock-storage --json
uv run ood update --knowledge-dir knowledge/mock/v1 --storage-dir data/mock-storage --json
```

Mock files are intentionally accepted as ordinary Markdown knowledge. The normal metadata warnings, duplicate diagnostics, runtime manifest, and fallback index artifacts remain active; there is no mock-only index command or bypass. `ood reindex` performs a clean rebuild of the selected `--storage-dir`, while `ood update` reports manifest diffs for added, changed, unchanged, and deleted mock files. Import and index validation is fully local and does not require Cloud LLM credentials.

## Evaluation Dataset and Metrics

The versioned fixture lives at `evaluation/datasets/mock-v1.json` and stores expected sources, forbidden sources, intent, routing, identifiers, command-risk expectations, and uncertainty labels outside indexed Markdown. Do not copy golden labels into `knowledge/` files; Markdown remains retrieval input, while JSON fixtures remain evaluation truth. `ood eval run` executes the dataset through the public `RagEngine.query()` contract, and `ood eval baseline`/`review`/`decide`/`update-baseline` provide the local feedback loop.

The metric functions are deterministic and local. Retrieval metrics cover Hit@1, Hit@3, Hit@5, MRR, source recall, and forbidden-source rate from ordered `SourceHit.path` values. Ticket-intelligence metrics compare public `TicketAnalysis` output for intent accuracy, routing accuracy, identifier recall, command-risk accuracy, and uncertainty accuracy.

### Baseline and review gate

Run the complete local loop with explicit mock paths:

```bash
uv run ood mock-init --target-dir knowledge/mock/v1 --dataset mock-v1
uv run ood reindex --knowledge-dir knowledge/mock/v1 --storage-dir data/mock-storage --json
uv run ood query "TraceId Kafka AKHQ Ersatzgeschäft" --knowledge-dir knowledge/mock/v1 --storage-dir data/mock-storage --verbose
uv run ood eval run --knowledge-dir knowledge/mock/v1 --storage-dir data/mock-storage --dataset evaluation/datasets/mock-v1.json --out data/evaluation/reports/mock-v1.json
uv run ood eval baseline --report data/evaluation/reports/mock-v1.json --out data/evaluation/baselines/current.json
uv run ood eval review --report data/evaluation/reports/mock-v1.json
uv run ood eval decide --review data/evaluation/reviews/mock-v1-<hash>.review.json --decision approved --reviewer YOUR_NAME --rationale "reviewed" --baseline-update requested
uv run ood eval update-baseline --report data/evaluation/reports/mock-v1.json --review data/evaluation/reviews/mock-v1-<hash>.review.json --out data/evaluation/baselines/current.json
```

The first baseline is observational: thresholds stay null and ordinary failed eval cases do not turn into process-level failures. Rejected or deferred reviews do not update the baseline; metric improvement alone is not accepted improvement.

Review cases include machine-readable proposed_fix_type and proposed_fix_notes fields; allowed proposed_fix_type values are corpus_fix, retrieval_fix, query_fix, dataset_fix, baseline_update, and investigate. Use proposed_fix_type to record the recommended corpus/query/retrieval/dataset/baseline-update follow-up, but it does not bypass the explicit review decision gate.

Generated reports, reviews, baselines, and storage artifacts belong under ignored `data/` paths unless you intentionally create a stable fixture for review.

## Ticket Intelligence

Use `ood query` with the full incoming ticket text to get structured operational triage:

```bash
uv run ood query "Police P-12345 Fehler beim Login"
```

Human output includes `Antwort`, `Einschätzung`, `Lösungsweg`, `Routing`, `Quellen`, `Unsicherheiten`, detected identifiers, and `Command Risks`. The same contract is available as JSON for automation:

```bash
uv run ood query "Police P-12345 Fehler beim Login" --json
```

The JSON payload preserves the top-level query, answer, confidence, source, `llm_used`, and status fields and adds nested `analysis` with intent, routing, identifiers, command-risk labels, uncertainties, solution steps, and mode. It also includes `retrieval_diagnostics` for skill use: backend, strategy, score components, graph retrieval status, and non-secret notes.

Default local queries use hybrid semantic+lexical retrieval. OOD combines local embedding cosine similarity with lexical exact-match signals so operational identifiers and terms such as `P-12345`, `ERR-502`, system names, components, and ticket vocabulary can lift the right source above vector-only matches. When sources are retrieved without Cloud LLM approval, OOD synthesizes a conservative extractive `Antwort` from top source excerpts and cites source ranks like `[1]` and `[2]`; it does not invent fix steps beyond cited evidence.

Privacy behavior: ticket analysis remains deterministic/retrieval-only by default and no ticket content is sent to a Cloud LLM. Configured credentials alone are not enough. Generated wording for `Einschätzung` and `Lösungsweg` is enabled only when `OOD_ALLOW_CLOUD_LLM=true` and Cloud LLM credentials are configured. Deterministic code still owns the trusted intent, routing, identifier, and command-risk labels.

Use `--verbose` on `ood query` to audit the runtime privacy decision:

```bash
uv run ood query "Police P-12345 Fehler beim Login" --verbose
```

Verbose human output includes `cloud_llm_allowed`, `llm_used`, retrieval backend/strategy, analysis mode, source count, graph status, graph artifact counts when active, and top-source fusion components. JSON output remains the stable `QueryResult` contract without CLI-only diagnostic wrappers.

### Graph retrieval

Local graph/metadata retrieval is active for the local fallback query path when `storage_dir` contains `ood-local-graph-index.json`. The artifact is generated next to `ood-local-vector-index.json` by `ood index`, `ood reindex`, and `ood update`. It is derived only from local Markdown/frontmatter/Wikilinks and stays under `storage_dir`, outside git.

Graph/metadata signals include frontmatter `title`, `type`, `service`, `system`, `component`/`komponente`, `keywords`, `keywords_de`, `keywords_en`, `aliases`, `tags`, and `related`; Markdown headings; command snippets under `## Commands`; outgoing Obsidian Wikilinks; incoming-link counts; and normalized search tokens. Queries fuse semantic/vector, lexical, metadata, graph, and final scores. Use `--verbose` to inspect these components; use `--json` to consume the same values from `retrieval_diagnostics.score_components` and `SourceHit.score_details`.

Example local OOD-KB workflow:

```bash
uv run ood reindex \
  --knowledge-dir /Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/articles \
  --storage-dir data/ood-kb-storage \
  --json

uv run ood query "TraceId Kafka AKHQ Ersatzgeschäft" \
  --storage-dir data/ood-kb-storage \
  --verbose
```

The smoke fixture `evaluation/datasets/ood-kb-traceid-smoke.json` captures the same query and expected source for the future Phase 13/14 black-box evaluation loop once those execution/reporting commands are available.

Cloud LLM approval is not required and not used for graph/metadata retrieval. If the graph artifact is missing or malformed, OOD degrades to semantic+lexical local retrieval and explains that fallback in `retrieval_diagnostics.graph_retrieval`.

Safety behavior: OOD Agent classifies commands as `grün`, `gelb`, `orange`, or `rot` and never executes commands. Risk output is advisory only so operators can review potentially destructive or privileged instructions before acting.

Override paths explicitly when your Markdown exports or runtime data live outside the repository:

```bash
uv run ood index --knowledge-dir /path/to/knowledge --storage-dir /path/to/data/storage --json
```

Plain `.md` files under `knowledge/` remain indexable; missing frontmatter is reported as warning-only metadata diagnostics. Missing or empty knowledge directories are successful no-ops per D-02 and report zero indexed documents. Cloud LLM credentials are optional per D-05/D-07: without credentials, queries return retrieval-only sources and confidence rationale without sending ticket content to a Cloud LLM. Real secrets belong only in `.env` or environment variables, never in Markdown sources or commits.

Verify the Core RAG CLI and service contracts with:

```bash
uv run pytest tests/test_cli.py tests/test_rag.py tests/test_models.py -q
```

## Directory defaults

OOD Agent uses a small local directory contract:

- `knowledge/` contains Markdown input files exported or curated from Wiki, ServiceNow, Jira, and notes.
- `data/` contains persisted runtime data and index files. This directory is excluded from git.
- `data/storage/` contains storage internals used by later retrieval/indexing plans.

## Configuration

Configuration precedence is: CLI arguments > environment variables > `.env` config file > defaults.

Copy `.env.example` to `.env` for local use and keep real credentials out of git. The typed settings loader accepts these `OOD_` variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `OOD_KNOWLEDGE_DIR` | `knowledge` | Markdown knowledge source directory. |
| `OOD_DATA_DIR` | `data` | Runtime data and index directory. |
| `OOD_STORAGE_DIR` | `data/storage` derived from `OOD_DATA_DIR` | Retrieval storage directory. |
| `OOD_LLM_PROVIDER` | unset | Cloud LLM provider name. |
| `OOD_LLM_API_KEY` | unset | Cloud LLM API key, loaded only from local configuration or environment. |
| `OOD_LLM_MODEL` | unset | Cloud LLM model name. |
| `OOD_ALLOW_CLOUD_LLM` | `false` | Explicit privacy approval gate for sending ticket or knowledge content to a Cloud LLM for answer synthesis. |
| `OOD_VERBOSE` | `0` | Verbosity level used by CLI commands. |
| `OOD_QUIET` | `false` | Suppress non-essential CLI output. |

`OOD_KNOWLEDGE_DIR`, `OOD_DATA_DIR`, and `OOD_STORAGE_DIR` may point outside the repository so local indexes and source exports can stay out of git. Real secrets belong only in `.env` or environment variables, never in Markdown sources, README examples, or commits. Keep `OOD_ALLOW_CLOUD_LLM=false` unless a documented privacy approval permits Cloud LLM synthesis for ticket content.

Use `-v/--verbose` for diagnostic context and `-q/--quiet` to suppress non-essential human output:

```bash
uv run ood update --verbose
uv run ood update --quiet
```

Each command accepts path overrides with the same precedence as other explicit CLI inputs:

```bash
uv run ood reindex \
  --knowledge-dir /path/to/knowledge \
  --data-dir /path/to/data \
  --storage-dir /path/to/storage
```
