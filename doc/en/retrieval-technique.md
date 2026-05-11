# OOD Agent Retrieval Technique

This document explains how OOD Agent stores Markdown knowledge, indexes it, and retrieves it for ticket queries. It describes the current local default path and distinguishes it from the optional LightRAG/Cloud LLM path.

## Target Architecture

OOD Agent is a local RAG assistant for ServiceNow triage. Markdown remains the canonical knowledge format. Runtime artifacts such as the manifest, vector index, and graph index live under `storage_dir`, typically `data/storage` or `data/ood-kb-storage`, and should not be committed.

The retrieval process balances three goals:

- find semantically similar solution articles
- rank exact operational terms such as ticket IDs, error codes, system names, and components highly
- use metadata and Wikilinks without sending ticket or wiki content to a Cloud LLM unless explicitly approved

## Knowledge Base Storage

The canonical knowledge base consists of Markdown files under `knowledge_dir`, which defaults to `knowledge/`. For the OOD-KB export, the path can be set to an external directory through `--knowledge-dir` or `OOD_KNOWLEDGE_DIR`.

Each file is treated as one knowledge unit:

- YAML frontmatter provides structured metadata such as `quelle`, `datum`, `status`, `system`, `komponente`, `title`, and `type`.
- The Markdown body is the main retrieval text.
- Empty bodies are skipped.
- Missing OOD metadata produces warnings but does not block indexing.

Index and diagnostic artifacts are stored separately in `storage_dir`:

| Artifact | Purpose |
| --- | --- |
| `ood-manifest.json` | Hashes, metadata, warnings, duplicate groups, and the diff basis for `update`. |
| `ood-local-vector-index.json` | Local vector index with path, content, excerpt, and embedding per document. |
| `ood-local-graph-index.json` | Local metadata/graph index with frontmatter fields, search tokens, and Wikilink edges. |

`data/` and other runtime storage locations should not be committed. Markdown sources remain the auditable source of truth.

## Crawling and Indexing

The `ood index`, `ood reindex`, and `ood update` commands share the same core flow:

1. OOD recursively discovers `*.md` files below `knowledge_dir`.
2. Files are sorted deterministically by path.
3. Frontmatter and body are split.
4. OOD creates `content_hash`, `body_hash`, a body excerpt, and metadata warnings for each document.
5. Exact and near duplicates are diagnosed.
6. Manifest, vector index, and graph index are written to `storage_dir`.

The commands differ in lifecycle behavior:

| Command | Behavior |
| --- | --- |
| `ood index` | Builds index artifacts without explicitly clearing existing storage. |
| `ood reindex` | Safely clears the configured storage directory and rebuilds everything. |
| `ood update` | Compares current hashes with the manifest and indexes new or changed files. |

`update` reports deleted sources as stale/deleted. Use `reindex` when deleted content must be fully cleaned from runtime artifacts.

## Embedding

The local default path uses `sentence-transformers` with `paraphrase-multilingual-MiniLM-L12-v2`. Embeddings have 384 dimensions and are generated with normalization enabled.

During local indexing, OOD creates one embedding for each Markdown body. The result is stored in `ood-local-vector-index.json` together with the path, content, and an excerpt capped at 500 characters. During a query, the query text is embedded with the same model.

When LightRAG is available and the local fallback is not active, OOD creates a LightRAG instance with the same local embedding model. The configured maximum embedding token window is 8192 tokens.

## Chunking

In the current local fallback, one Markdown document is stored as one retrieval unit. In this path, the term `chunks` in status and query output effectively means the stored document units in the local vector index.

Excerpts are capped at 500 characters so CLI and JSON output stay focused. OOD does not print the complete source text by default. Operators open the cited Markdown file if they need full context.

In the LightRAG path, LightRAG may return internally created chunks. OOD then normalizes those chunks into the stable `SourceHit` contract with path, score, and excerpt.

## Graph Construction

Alongside the vector index, OOD writes the local graph index `ood-local-graph-index.json`. This graph is derived deterministically from Markdown, frontmatter, and Wikilinks.

For each document, OOD stores data including:

- `title`, `type`, `service`, `system`, `component` or `komponente`
- `keywords`, `keywords_de`, `keywords_en`, `aliases`, `tags`, and `related`
- Markdown headings
- commands from `## Commands`, `## Befehle`, or `## Kommandos`
- outgoing Wikilinks
- incoming link count
- normalized `search_tokens`
- body excerpt

Wikilinks are stored as `source -> target` edges labeled `wikilink`. Targets are resolved by file stem or title slug. If no target document is found, OOD records a slug path such as `target.md` as the edge target.

## Retrieval Process

When `ood query "..."` runs, OOD first checks whether index artifacts exist in the selected `storage_dir`. It then follows one of two main paths.

The local default path is used when no Cloud LLM is approved and no LightRAG backend is used:

1. OOD reads `ood-local-vector-index.json`.
2. The query text is embedded locally.
3. Query tokens are normalized.
4. If available, `ood-local-graph-index.json` is loaded.
5. Each document receives semantic, lexical, metadata, and graph scores.
6. The top 5 sources are returned as `SourceHit` values.
7. Without a Cloud LLM, OOD creates a conservative extractive answer from the best excerpts.
8. Ticket intelligence locally determines intent, routing, identifiers, command risks, and uncertainties.

The LightRAG path is used when LightRAG is available. Without Cloud LLM approval, OOD uses `QueryParam(mode="naive")`; with privacy approval and a supported provider, OOD uses `mode="mix"` and may additionally request a generated answer. In both cases, OOD normalizes sources into its own `QueryResult` contract.

## Ranking and Scoring

In the local path, ranking is a hybrid fusion. Without an active graph index, OOD uses:

| Component | Weight |
| --- | ---: |
| Semantic cosine similarity between query and document | 0.65 |
| Lexical token coverage | 0.35 |
| Exact operational token boost | up to 0.35 |

With an active graph index, the weighting expands:

| Component | Weight |
| --- | ---: |
| Semantic | 0.20 |
| Lexical | 0.15 |
| Metadata | 0.40 |
| Graph signals | 0.25 |
| Exact operational token boost | up to 0.35 |

The final score is capped at `1.0`. Result-list scores are rounded to two decimal places. For each source, OOD also stores `score_details` with individual components, matches, and weights.

Lexical scoring measures how many query tokens occur in the document. Tokens with numbers, hyphens, or very short operational terms are treated as exact operational hits and can trigger a boost. This helps terms such as `P-12345`, `ERR-502`, `AKHQ`, and component-specific abbreviations.

Metadata scoring uses weighted matches in fields such as title, type, service, system, component, keywords, aliases, tags, headings, commands, and search tokens. Graph signals use outgoing Wikilinks, incoming links, and matches in linked target documents.

## Diagnostics

`ood query --verbose` and `ood query --json` expose retrieval diagnostics:

- `backend`: `local_vector_index`, `local_vector_graph_index`, or `lightrag`
- `strategy`: selected retrieval strategy
- `score_components`: score breakdown per source
- `graph_retrieval`: status, artifact path, document and edge counts, or fallback reason
- `notes`: short notes about retrieval behavior

If the graph index is missing or malformed, OOD automatically falls back to hybrid semantic+lexical retrieval and reports that state in `graph_retrieval`.

## Privacy Boundary

Local indexing, local embeddings, graph construction, scoring, routing, and command-risk classification do not require Cloud LLM approval. Ticket and wiki content stays local.

A Cloud LLM may only be used when `OOD_ALLOW_CLOUD_LLM=true` is set and valid credentials are configured. Credentials alone are not enough. Without approval, OOD stays retrieval-only and creates answers only from local sources.
