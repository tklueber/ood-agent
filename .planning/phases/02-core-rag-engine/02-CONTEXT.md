# Phase 2: Core RAG Engine - Context

**Gathered:** 2026-05-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 replaces the Phase 1 CLI stubs with real Core RAG behavior: users can index Markdown files from the configured `knowledge_dir`, query the resulting LightRAG-backed knowledge base with semantic search, and receive source-attributed results with relevance scores and answer confidence.

**In scope:** Initial Markdown indexing, clean reindexing, LightRAG integration, semantic query execution, source attribution, relevance scores, confidence scoring, and CLI output contracts for `index`, `query`, and `reindex`.

**Out of scope:** Incremental updates, duplicate detection, YAML metadata enforcement, knowledge lifecycle/API, ticket intent/routing, policy/offert number extraction, command risk classification, Teams/web UI, and tool execution.

</domain>

<decisions>
## Implementation Decisions

### Indexing Behavior
- **D-01:** `ood index` must discover and index all `*.md` files recursively under the configured `knowledge_dir`.
- **D-02:** If `knowledge_dir` is missing or contains no Markdown files, `ood index` should exit successfully with a friendly no-op message and report zero indexed documents.
- **D-03:** Phase 2 must accept plain Markdown without YAML frontmatter. Frontmatter conventions and metadata validation remain Phase 3 scope.
- **D-04:** `ood reindex` must perform a clean rebuild by clearing the selected LightRAG storage area and rebuilding from the current Markdown files.

### LLM and Privacy Behavior
- **D-05:** `ood query` should call a Cloud LLM only when LLM credentials are configured. If no credentials exist, it must still provide retrieval-only results.
- **D-06:** When Cloud LLM usage is enabled, the query flow may send the user query plus the full retrieved source documents to the Cloud LLM for grounded answer generation.
- **D-07:** Missing LLM credentials must degrade gracefully: return ranked sources and clearly state that generated answer/confidence quality is limited or unavailable because no LLM is configured.
- **D-08:** Phase 2 confidence scoring should be heuristic, based on retrieval signal such as score strength, score spread, source count, and LLM availability rather than relying only on LLM self-rating.

### LightRAG Storage Shape
- **D-09:** LightRAG storage internals should be opaque to users. The stable user-facing contract is the configurable `storage_dir`, not the internal artifact layout.
- **D-10:** Default LightRAG artifacts should be stored under the already-established `data/storage` derived from `Settings.storage_dir`.
- **D-11:** `ood index` should reuse existing storage and update/add documents on a best-effort basis where LightRAG supports it. Clean deletion is reserved for `ood reindex`.
- **D-12:** Storage diagnostics such as storage path, document counts, or internal state should appear only in `--verbose` output and/or `--json`, not as normal human-output noise.

### Query Output Contract
- **D-13:** Default human-mode `ood query <text>` should return a verbose analysis: generated answer when available, confidence, confidence rationale, ranked sources, relevance scores, and useful excerpts. If running retrieval-only, it should explain that no generated answer is available and still show sources.
- **D-14:** `ood query --json` must use a stable schema suitable for automation and tests, including at least: `query`, `answer` or `null`, `confidence`, `sources`, `llm_used`, and `status`.
- **D-15:** Each JSON source entry should include at least `path`, `score`, and `excerpt`. Paths should be relative to the configured `knowledge_dir`, not absolute filesystem paths.
- **D-16:** If `ood query` runs before an index exists, it should fail non-zero with a clear instruction to run `ood index` first rather than silently returning empty results.

### the agent's Discretion
- Exact LightRAG adapter structure, embedding/LLM provider integration details, prompt wording, and internal confidence formula are left to research and planning as long as the user-visible decisions above hold.
- Exact normal-mode wording, JSON field ordering, excerpt length, and Rich formatting are flexible as long as tests can assert the stable contract.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Scope and Requirements
- `.planning/ROADMAP.md` §Phase 2: Core RAG Engine — Defines the fixed phase goal, success criteria, dependency on Phase 1, and mapped requirements.
- `.planning/REQUIREMENTS.md` §Core RAG and §Infrastructure — Defines RAG-01 through RAG-05 plus INF-01, INF-03, and INF-04 for this phase.
- `.planning/PROJECT.md` §Constraints and §Context — Defines Markdown-first knowledge format, local MVP, Cloud LLM privacy constraint, and CLI-first architecture.

### Prior Decisions
- `.planning/phases/01-foundation-cli/01-CONTEXT.md` — Locks uv/Python 3.10+, Typer CLI, flat command names, config precedence, `knowledge/`, `data/`, `data/storage`, `--json`, `--verbose`, and `--quiet` conventions.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/ood/cli.py` — Existing Typer app exposes `index`, `update`, `query`, and `reindex`; Phase 2 should replace stub internals while preserving command names and shared options.
- `src/ood/config.py` — `Settings` already provides `knowledge_dir`, `data_dir`, derived `storage_dir`, LLM provider/model/API key fields, and `has_llm_credentials`.
- `tests/test_cli.py` — Establishes current CLI output modes and path override behavior; Phase 2 should update these tests from stub assertions to real RAG behavior.
- `tests/test_config.py` — Locks config precedence and supported `OOD_` variables for paths and LLM credentials.
- `pyproject.toml` — Uses uv-compatible Python package metadata, strict mypy, ruff, pytest, and `ood = "ood.cli:app"` console script.

### Established Patterns
- CLI uses Typer with a flat command structure and shared options per command.
- Human output uses Rich Console by default; `--json` emits machine-parseable JSON; `--quiet` suppresses non-essential human output; `--verbose` exposes diagnostics.
- Settings are loaded from defaults, `.env`, `OOD_` environment variables, and explicit CLI overrides.
- Runtime data and indexes must stay outside git under configurable local paths.

### Integration Points
- `index` and `reindex` should load `Settings`, read from `settings.knowledge_dir`, and write LightRAG artifacts under `settings.storage_dir`.
- `query` should load `Settings`, use the existing storage directory, and branch between LLM-backed answer generation and retrieval-only output based on `settings.has_llm_credentials`.
- The current stub helper structure in `src/ood/cli.py` can either be refactored into service functions or kept thin while new RAG modules handle indexing/query logic.

</code_context>

<specifics>
## Specific Ideas

- Phase 2 should stay forgiving for local MVP use: plain Markdown is valid, empty/missing knowledge dirs do not fail indexing, and missing LLM credentials do not block retrieval.
- The user prefers a rich human `query` result by default, not a minimal search listing.
- Full retrieved source documents may be sent to the configured Cloud LLM when LLM usage is enabled.
- `reindex` is the explicit destructive rebuild command; `index` should not silently clear existing storage.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-core-rag-engine*
*Context gathered: 2026-05-01*
