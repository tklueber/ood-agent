# Tutorial: Index and query OOD wiki exports

This tutorial shows the fastest local workflow for indexing the wiki exports from `/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw` with OOD Agent and using them for ticket queries.

## Prerequisites

- Repository: `/Users/timo/01_dev/projects/ood-agent`
- Wiki export: `/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw`
- Dependencies are installed with `uv`.
- Cloud LLM access is optional. Without `OOD_LLM_API_KEY`, OOD runs in local retrieval-only mode and does not send ticket or wiki content to a Cloud LLM.

## 1. Install dependencies

First change into the project directory:

```bash
cd /Users/timo/01_dev/projects/ood-agent
```

Optionally verify that the wiki export contains Markdown files:

```bash
ls "/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw"
```

Then install the project dependencies:

```bash
uv sync
```

## 2. Rebuild the index from the wiki export

Use `reindex` for the first run so the storage directory contains only this wiki export.

```bash
uv run ood reindex \
  --knowledge-dir "/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw" \
  --storage-dir "data/ood-kb-storage" \
  --json
```

Expected result: the JSON output reports indexed Markdown files, the effective `storage_dir`, metadata warnings if any, and the manifest path. The raw files do not need to be moved.

## 3. Run the first query

```bash
uv run ood query \
  "Offer is stuck in return processing, what should I check?" \
  --storage-dir "data/ood-kb-storage"
```

The output contains:

- assessment
- solution steps
- routing
- confidence
- sources
- uncertainties
- detected identifiers and command risks

## 4. Use JSON output for automation

```bash
uv run ood query \
  "How do I reset the ZEPAS sync?" \
  --storage-dir "data/ood-kb-storage" \
  --json
```

## 5. Index later changes incrementally

When new or changed Markdown files appear under `raw/`, `update` is usually enough:

```bash
uv run ood update \
  --knowledge-dir "/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw" \
  --storage-dir "data/ood-kb-storage" \
  --json
```

`update` compares file hashes against `data/ood-kb-storage/ood-manifest.json` and indexes only new or changed files. Deleted files are reported as stale/deleted; run `reindex` afterwards if you need a clean rebuild.

## 6. Optional: configure paths permanently

Create a local `.env` file in the repository. Do not commit this file.

```dotenv
OOD_KNOWLEDGE_DIR=/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw
OOD_STORAGE_DIR=data/ood-kb-storage
```

After that, shorter commands are enough:

```bash
uv run ood reindex --json
uv run ood query "Discount menu is not visible"
uv run ood update --json
```

## 7. Privacy notes

- Do not store secrets in Markdown sources, README files, documentation, or commits.
- Without `OOD_LLM_API_KEY`, OOD uses local fallback/retrieval logic.
- With `OOD_LLM_API_KEY`, ticket text may be sent to the configured Cloud LLM provider for generated wording. Use this only after privacy approval.
- Runtime data under `data/` stays outside git.

## 8. Quick verification

```bash
uv run pytest tests/test_cli.py tests/test_rag.py tests/test_models.py -q
```

If this test and a sample query succeed, the wiki export is available locally through the index.
