# Manual: OOD Agent with wiki extraction from `raw/`

This manual describes the complete local workflow for indexing OOD wiki exports from `/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw`, keeping the index current, and using it for operational ticket queries.

## Purpose

OOD Agent is a local RAG assistant for ServiceNow triage. It searches curated Markdown knowledge sources and returns actionable suggestions with source references, routing assessment, confidence, and safety labels for commands found in the retrieved content.

The relevant wiki export lives here:

```text
/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw
```

The files are regular Markdown files with YAML frontmatter, for example Confluence ID, Confluence URL, and synchronization timestamp. OOD also accepts files without full OOD-specific frontmatter; missing OOD metadata is reported as warnings only and does not block indexing.

## Directory and data model

| Path | Meaning |
| --- | --- |
| `/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw` | Canonical raw wiki export for this workflow. |
| `data/ood-kb-storage` | Recommended local index storage for the `raw` export. |
| `data/ood-kb-storage/ood-manifest.json` | Manifest with file hashes, indexing state, and diff data for `update`. |
| `doc/de` and `doc/en` | Repository documentation in German and English. |

`data/` is runtime storage and should not be committed.

## Installation

Run this in the repository:

```bash
uv sync
```

Optional test run:

```bash
uv run pytest -q
```

## Configuration

Configuration precedence:

1. CLI arguments
2. Environment variables
3. `.env`
4. Defaults

Important variables:

| Variable | Purpose |
| --- | --- |
| `OOD_KNOWLEDGE_DIR` | Markdown source directory. For this workflow: `/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw`. |
| `OOD_DATA_DIR` | General runtime directory. Default: `data`. |
| `OOD_STORAGE_DIR` | Concrete index storage. Recommended: `data/ood-kb-storage`. |
| `OOD_LLM_PROVIDER` | Optional Cloud LLM provider. |
| `OOD_LLM_API_KEY` | Optional API key. Store only in local `.env` or the environment. |
| `OOD_LLM_MODEL` | Optional Cloud LLM model. |

Recommended local `.env`:

```dotenv
OOD_KNOWLEDGE_DIR=/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw
OOD_STORAGE_DIR=data/ood-kb-storage
```

Never store real credentials in Markdown files or commits.

## Indexing strategy

OOD provides three indexing commands:

| Command | Use case |
| --- | --- |
| `index` | Initial indexing without explicitly clearing existing storage artifacts. |
| `reindex` | Clean index rebuild. Recommended for the first run and for cleanup after deleted sources. |
| `update` | Incremental update based on the manifest. Recommended for ongoing maintenance. |

## Complete CLI reference

All current OOD features are available through `uv run ood ...`.

| Command | Purpose | Typical use |
| --- | --- | --- |
| `ood index` | Builds an index from Markdown files. | First ingestion of a new source directory when existing storage artifacts do not need to be explicitly cleared. |
| `ood reindex` | Clears the selected storage directory and rebuilds the index from scratch. | First production run for the wiki export, larger export changes, cleanup after deleted sources. |
| `ood update` | Compares current Markdown files with the manifest and indexes new/changed files. | Ongoing maintenance after small wiki export changes. |
| `ood query "..."` | Queries the existing index with ticket text or a domain question. | Operational ServiceNow triage, source lookup, routing and risk assessment. |
| `ood mock-init` | Generates a deterministic synthetic mock corpus. | Privacy-safe tests and evaluation without real wiki or ticket data. |
| `ood mock-validate` | Validates mock markers, safety findings, and coverage. | Check whether mock data is clearly synthetic and free of golden-answer leakage. |

### Shared output and diagnostics options

| Option | Commands | Effect |
| --- | --- | --- |
| `--json` | all commands | Emits machine-readable JSON instead of human output. |
| `-v`, `--verbose` | `index`, `reindex`, `update`, `query`, `mock-validate` | Shows diagnostic context; configuration errors expose more detail. |
| `-q`, `--quiet` | all commands | Suppresses non-essential human output. |

### Path options for real knowledge data

These options apply to `index`, `reindex`, `update`, and `query`.

| Option | Meaning |
| --- | --- |
| `--knowledge-dir PATH` | Markdown source directory. For this workflow: `/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw`. For `query`, this is only relevant while settings are loaded; retrieval uses the selected storage. |
| `--data-dir PATH` | General runtime directory. If `--storage-dir` is not set, OOD derives `PATH/storage`. |
| `--storage-dir PATH` | Concrete index/retrieval storage directory. For `query`, it must match the storage used by the previous `index`/`reindex`/`update`. |

### Mock corpus options

| Command | Option | Meaning |
| --- | --- | --- |
| `mock-init` | `--target-dir PATH` | Target directory for generated mock Markdown files. Default: `knowledge/mock/v1`. |
| `mock-init` | `--dataset NAME` | Dataset name written to frontmatter. Default: `mock-v1`. |
| `mock-validate` | `--corpus-dir PATH` | Directory containing mock Markdown files. Default: `knowledge/mock/v1`. |

### JSON contracts

`index` and `reindex` return `command`, `status`, `indexed_documents`, `skipped_documents`, `storage_dir`, `message`, optional `metadata_warnings`, optional `duplicate_groups`, and optional `manifest_path` in JSON mode.

`update` additionally returns `diff` with `new_paths`, `changed_paths`, `unchanged_paths`, `deleted_paths`, and `skipped_paths`, plus `schema_version`.

`query` returns `query`, `answer`, `confidence`, `sources`, `llm_used`, `status`, and `analysis`. `analysis` contains `intent`, `assessment`, `solution_steps`, `routing`, `identifiers`, `command_risks`, `uncertainties`, and `mode`.

`mock-init` returns `dataset`, `target_dir`, `document_count`, `generated_paths`, and `source_types`.

`mock-validate` returns `corpus_dir`, `document_count`, `is_safe`, `findings`, and `coverage` by `source_types`, `systems`, `components`, `routing_targets`, `command_risks`, and `scenario_categories`.

### What OOD intentionally does not do

- OOD never executes retrieved commands. Commands are classified only.
- `update` does not guarantee removal of deleted sources from every storage artifact; use `reindex` for that.
- Without a Cloud LLM, OOD does not perform external text generation; it returns local retrieval/fallback answers.
- Golden answers, expected sources, and evaluation expectations do not belong in indexed Markdown files.
- Secrets must never be stored in Markdown, README files, documentation, or commits.

## Initial clean indexing

```bash
uv run ood reindex \
  --knowledge-dir "/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw" \
  --storage-dir "data/ood-kb-storage" \
  --json
```

The output includes:

- number of indexed documents
- skipped empty documents
- metadata warnings
- duplicate groups
- storage path
- manifest path

## Incremental updates

```bash
uv run ood update \
  --knowledge-dir "/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw" \
  --storage-dir "data/ood-kb-storage" \
  --json
```

`update` reports new, changed, unchanged, and deleted paths. Deleted files are not automatically removed from every storage artifact. Run `reindex` when deleted sources must be fully cleaned up.

## Querying

Human-readable output:

```bash
uv run ood query \
  "Broker cannot see his policy in the SLS marketplace" \
  --storage-dir "data/ood-kb-storage"
```

JSON output:

```bash
uv run ood query \
  "How do I resolve missing invoices or policy documents?" \
  --storage-dir "data/ood-kb-storage" \
  --json
```

Query results contain:

| Field | Meaning |
| --- | --- |
| `answer` | Answer text or retrieval-only summary. |
| `confidence` | Score and rationale for retrieval quality. |
| `sources` | Retrieved Markdown sources with path, score, and excerpt. |
| `analysis.intent` | Deterministically detected ticket intent. |
| `analysis.routing` | Routing suggestion with rationale. |
| `analysis.identifiers` | Detected policy, offer, or ticket identifiers. |
| `analysis.command_risks` | Safety classification for commands. |
| `llm_used` | Shows whether a Cloud LLM was used. |

## Privacy and runtime mode

Without `OOD_LLM_API_KEY`, OOD uses local retrieval/fallback logic. No ticket or wiki content is sent to a Cloud LLM.

With `OOD_LLM_API_KEY`, OOD may use generated wording for assessment and solution steps. Use this only after privacy approval. Deterministic analysis elements such as routing, identifiers, and command-risk classification remain owned by the OOD code.

## Source quality

For best diagnostics, each Markdown document can include OOD frontmatter:

```yaml
---
quelle: wiki
status: active
system: helix-mf
komponente: servicedesk
type: howto
---
```

The existing `raw` files with Confluence metadata remain indexable. Missing fields are warnings, not errors.

## Troubleshooting

| Problem | Cause | Fix |
| --- | --- | --- |
| `IndexMissingError` during `query` | No index exists in the selected storage. | Run `reindex` first with the same `--storage-dir`. |
| No results or low confidence | Query is too generic or storage path is wrong. | Use more concrete ticket text and verify `--storage-dir`. |
| Many metadata warnings | Raw export does not contain all OOD frontmatter fields. | Accept warnings or enrich files with OOD frontmatter later. |
| Deleted sources appear in diagnostics | `update` only reports stale/deleted paths. | Run `reindex` for a clean rebuild. |
| Cloud LLM must not be used | `OOD_LLM_API_KEY` is configured. | Remove the key from the environment or `.env`. |

## Recommended daily workflow

```bash
uv run ood update --json
uv run ood query "Paste ticket text here" --storage-dir "data/ood-kb-storage"
```

After larger wiki export changes:

```bash
uv run ood reindex --json
```

## Verification

```bash
uv run pytest tests/test_cli.py tests/test_rag.py tests/test_models.py -q
```

This verifies CLI and RAG contracts, not the business completeness of the wiki export.
