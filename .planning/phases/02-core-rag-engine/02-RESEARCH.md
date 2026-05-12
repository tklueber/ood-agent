# Phase 02: Core RAG Engine - Research

**Researched:** 2026-05-01  
**Domain:** Python CLI RAG integration with LightRAG Core, Markdown indexing, semantic retrieval, source attribution  
**Confidence:** MEDIUM-HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Indexing Behavior
- **D-01:** `ood index` must discover and index all `*.md` files recursively under the configured `knowledge_dir`.
- **D-02:** If `knowledge_dir` is missing or contains no Markdown files, `ood index` should exit successfully with a friendly no-op message and report zero indexed documents.
- **D-03:** Phase 2 must accept plain Markdown without YAML frontmatter. Frontmatter conventions and metadata validation remain Phase 3 scope.
- **D-04:** `ood reindex` must perform a clean rebuild by clearing the selected LightRAG storage area and rebuilding from the current Markdown files.

#### LLM and Privacy Behavior
- **D-05:** `ood query` should call a Cloud LLM only when LLM credentials are configured. If no credentials exist, it must still provide retrieval-only results.
- **D-06:** When Cloud LLM usage is enabled, the query flow may send the user query plus the full retrieved source documents to the Cloud LLM for grounded answer generation.
- **D-07:** Missing LLM credentials must degrade gracefully: return ranked sources and clearly state that generated answer/confidence quality is limited or unavailable because no LLM is configured.
- **D-08:** Phase 2 confidence scoring should be heuristic, based on retrieval signal such as score strength, score spread, source count, and LLM availability rather than relying only on LLM self-rating.

#### LightRAG Storage Shape
- **D-09:** LightRAG storage internals should be opaque to users. The stable user-facing contract is the configurable `storage_dir`, not the internal artifact layout.
- **D-10:** Default LightRAG artifacts should be stored under the already-established `data/storage` derived from `Settings.storage_dir`.
- **D-11:** `ood index` should reuse existing storage and update/add documents on a best-effort basis where LightRAG supports it. Clean deletion is reserved for `ood reindex`.
- **D-12:** Storage diagnostics such as storage path, document counts, or internal state should appear only in `--verbose` output and/or `--json`, not as normal human-output noise.

#### Query Output Contract
- **D-13:** Default human-mode `ood query <text>` should return a verbose analysis: generated answer when available, confidence, confidence rationale, ranked sources, relevance scores, and useful excerpts. If running retrieval-only, it should explain that no generated answer is available and still show sources.
- **D-14:** `ood query --json` must use a stable schema suitable for automation and tests, including at least: `query`, `answer` or `null`, `confidence`, `sources`, `llm_used`, and `status`.
- **D-15:** Each JSON source entry should include at least `path`, `score`, and `excerpt`. Paths should be relative to the configured `knowledge_dir`, not absolute filesystem paths.
- **D-16:** If `ood query` runs before an index exists, it should fail non-zero with a clear instruction to run `ood index` first rather than silently returning empty results.

### the agent's Discretion
- Exact LightRAG adapter structure, embedding/LLM provider integration details, prompt wording, and internal confidence formula are left to research and planning as long as the user-visible decisions above hold.
- Exact normal-mode wording, JSON field ordering, excerpt length, and Rich formatting are flexible as long as tests can assert the stable contract.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RAG-01 | System can index Markdown files from knowledge/ directory | Use recursive `Path.rglob("*.md")`, read UTF-8 text, pass document contents plus relative `file_paths` to LightRAG. Empty/missing directories are successful zero-doc no-ops. |
| RAG-02 | System supports semantic search over indexed tickets | Use LightRAG `query_data` / `aquery_data` with `QueryParam(mode="mix")` for graph+vector retrieval; use `mode="naive"` as retrieval-only fallback when LLM-backed graph/query generation is unavailable. |
| RAG-03 | Query results include source attribution with relevance scores | Insert with `file_paths`; LightRAG stores `file_path` in chunks/entities/relationships and exposes references/chunks. Planner should add an OOD source-normalization layer and derive/attach scores from vector hits or deterministic ranking. |
| RAG-04 | System provides confidence scoring for generated answers | Implement heuristic confidence in OOD layer from top score, score spread, source count, status, and `llm_used`; do not rely on LLM self-rating alone. |
| RAG-05 | System uses LightRAG for dual-level graph + vector retrieval | Use `lightrag-hku` Core `LightRAG` with default local stores: `JsonKVStorage`, `NanoVectorDBStorage`, `NetworkXStorage`, `JsonDocStatusStorage`, and `QueryParam(mode="mix")`. |
| INF-01 | CLI provides `index` command to build initial knowledge base | Replace `src/ood/cli.py` stub with service call; preserve Typer flat command and output flags. |
| INF-03 | CLI provides `query` command for ticket analysis | Replace query stub with RAG service, JSON schema, non-zero missing-index behavior, and Rich human output. |
| INF-04 | CLI provides `reindex` command to rebuild from scratch | Clear only `settings.storage_dir` and rebuild; keep `data_dir` and `.env` untouched. |
</phase_requirements>

## Summary

Phase 2 should introduce a thin OOD-owned RAG service layer around LightRAG Core rather than embedding LightRAG calls directly inside Typer command functions. LightRAG's Core API is appropriate for this local CLI MVP: it persists data under a `working_dir`, supports local JSON/NanoVectorDB/NetworkX storage by default, accepts `file_paths` for citation traceability, and exposes structured retrieval via `query_data` / `aquery_data` plus generated-answer flow via `query_llm` / `aquery_llm`.

The main planning risk is the product requirement to degrade gracefully without Cloud LLM credentials. Official LightRAG documentation states that both an LLM and embedding model are required for normal document indexing/querying, and graph extraction is LLM-backed. To satisfy privacy constraints, plan a two-lane adapter: **full LightRAG graph+vector mode when LLM credentials exist**, and **retrieval-only LightRAG vector mode with local embeddings and no Cloud LLM** when credentials are absent. The OOD layer should own stable CLI/JSON contracts, source normalization, relevance display, confidence scoring, and missing-index/no-doc behavior.

**Primary recommendation:** Use `lightrag-hku==1.4.15` behind `src/ood/rag.py`, store artifacts in `Settings.storage_dir`, insert Markdown with relative `file_paths`, query with `QueryParam(mode="mix")` when LLM is configured and `mode="naive"` for retrieval-only fallback, then normalize all results into OOD-owned dataclasses before CLI rendering.

## Project Constraints (from AGENTS.md / CLAUDE.md)

- No project-local `AGENTS.md` exists; global `/Users/timo/AGENTS.md` applies.
- Primary documentation language may be German, but code comments and commit messages should be English.
- Conventional Commits required if committing (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`).
- Shell scripts must use `set -euo pipefail` and check dependencies up front.
- Never commit secrets or `.env` / API keys; credentials must stay in `.env` / environment.
- No destructive Git operations or `rm -rf` without explicit confirmation.
- CLAUDE.md project constraints: Python + LightRAG + Cloud LLM after privacy approval; Markdown remains canonical; ticket content may go to Cloud LLM only when approved/configured; MVP runs locally; runtime indexes stay outside git.
- Phase 2 exception to future canonical metadata: plain Markdown without YAML frontmatter is valid now; YAML frontmatter validation is Phase 3 scope.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | >=3.10; project uv env observed 3.11.14 | Runtime | LightRAG README declares Python 3.10 support; project already requires `>=3.10`. |
| uv | 0.9.7 observed | Dependency management / command runner | Phase 1 locked uv and committed lockfile workflow. |
| lightrag-hku | 1.4.15, uploaded 2026-04-19 | Graph + vector RAG engine | Official package for HKUDS LightRAG Core; supports local default storage, source file paths, `QueryParam`, `query_data`, and `query_llm`. |
| Typer | existing `>=0.12.0` | CLI commands | Already established in Phase 1; preserve flat commands and shared options. |
| Rich | existing `>=13.7.0` | Human output | Already established for human-mode CLI output. |
| pydantic-settings | existing `>=2.2.0` | Configuration | Already established `Settings` with `OOD_` env prefix, `.env`, paths, and LLM credential flags. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sentence-transformers | 5.4.1, uploaded 2026-04-14 | Local embeddings without Cloud LLM credentials | Recommended fallback to preserve semantic retrieval without sending ticket text to cloud. Use a small multilingual/local embedding model; lock model name because reindex is required when embedding dimensions change. |
| numpy | 2.4.4, uploaded 2026-03-29 | Embedding vector arrays | Required by custom embedding wrappers and many embedding providers. |
| openai | 2.33.0, uploaded 2026-04-28 | Optional OpenAI-compatible LLM/embeddings | Only if `OOD_LLM_PROVIDER` / API key are configured and privacy-approved. LightRAG has OpenAI-compatible helpers. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Embedded LightRAG Core | LightRAG REST API Server | REST server has richer reference APIs, but adds a daemon/process and auth/config complexity. Phase 2 is local CLI-first; Core is simpler. |
| `QueryParam(mode="mix")` | `hybrid`, `local`, `global`, `naive` | `mix` is current documented KG + vector mode and reranker-friendly; `naive` is useful only for retrieval-only fallback. |
| Default local stores | PostgreSQL/Neo4j/Qdrant/OpenSearch | Production-capable but overkill for local MVP; default stores match `data/storage` and require no external services. |
| Cloud embeddings only | Local embeddings via sentence-transformers | Cloud embeddings are high quality but violate graceful no-credential/privacy fallback; local embeddings add dependency weight but keep retrieval working. |

**Installation:**
```bash
uv add lightrag-hku sentence-transformers numpy
# Optional only when provider integration is implemented:
uv add openai
```

**Version verification:** Python package versions were verified from PyPI on 2026-05-01 via JSON API / `pip index`. `pip index` under system Python 3.9 reported `lightrag-hku 1.3.9`, but PyPI and the project uv Python 3.11 environment support current `1.4.15`; use uv/Python >=3.10 for dependency resolution.

## Architecture Patterns

### Recommended Project Structure
```text
src/ood/
├── cli.py          # Typer command parsing, output mode handling only
├── config.py       # Existing Settings and load_settings
├── rag.py          # LightRAG adapter, indexing/query/reindex orchestration
├── models.py       # OOD-owned dataclasses: IndexResult, QueryResult, SourceHit
└── output.py       # JSON payload shaping and Rich human rendering, if cli.py grows
tests/
├── test_cli.py     # CLI contracts and JSON/human modes
├── test_rag.py     # RAG service behavior with temp dirs and small Markdown corpus
└── test_config.py  # Existing config contract
```

### Pattern 1: Thin CLI, Typed Service Layer
**What:** Typer loads settings, calls `RagEngine`, and renders returned OOD dataclasses. LightRAG-specific result shapes do not leak into CLI tests.  
**When to use:** All `index`, `query`, and `reindex` implementations in Phase 2.  
**Example:**
```python
# Source: OOD architecture recommendation based on existing Typer pattern
settings = _load_valid_settings(...)
engine = RagEngine(settings)
result = engine.index_markdown()
emit_index_result(result, json_output=json_output, quiet=quiet, verbose=verbose)
```

### Pattern 2: Explicit LightRAG Lifecycle
**What:** Create LightRAG with `working_dir=str(settings.storage_dir)`, call `await rag.initialize_storages()` before use, and `await rag.finalize_storages()` in `finally`.  
**When to use:** Every adapter method that opens LightRAG.  
**Example:**
```python
# Source: https://raw.githubusercontent.com/HKUDS/LightRAG/main/docs/ProgramingWithCore.md
rag = LightRAG(
    working_dir=str(settings.storage_dir),
    embedding_func=embedding_func,
    llm_model_func=llm_model_func,
)
await rag.initialize_storages()
try:
    await rag.ainsert(documents, ids=ids, file_paths=relative_paths)
finally:
    await rag.finalize_storages()
```

### Pattern 3: Source Attribution via `file_paths`
**What:** Read Markdown documents yourself and pass matching relative file paths to LightRAG insert.  
**When to use:** All indexing paths.  
**Example:**
```python
# Source: LightRAG ProgramingWithCore.md "Citation Functionality"
documents = [path.read_text(encoding="utf-8") for path in md_files]
file_paths = [path.relative_to(settings.knowledge_dir).as_posix() for path in md_files]
await rag.ainsert(documents, ids=file_paths, file_paths=file_paths)
```

### Pattern 4: OOD-Owned Result Normalization
**What:** Convert LightRAG `query_data` / `query_llm` responses into stable `SourceHit(path, score, excerpt)` objects and a stable JSON payload.  
**When to use:** `ood query` human and JSON modes.  
**Example:**
```python
# Source: LightRAG 1.4.15 aquery_data docs in lightrag.py
data = await rag.aquery_data(query, QueryParam(mode="mix", top_k=10, chunk_top_k=10))
chunks = data.get("data", {}).get("chunks", [])
sources = normalize_chunks_to_source_hits(chunks, knowledge_dir=settings.knowledge_dir)
```

### Anti-Patterns to Avoid
- **Putting LightRAG internals in CLI tests:** LightRAG storage layout is not stable user contract; test OOD payloads and behavior instead.
- **Assuming `index` can safely delete storage:** Only `reindex` may clear storage; `index` should best-effort add/update.
- **Sending queries to Cloud LLM just because provider package exists:** Gate on `settings.has_llm_credentials` and provider settings.
- **Embedding absolute source paths:** JSON sources must be relative to `knowledge_dir`.
- **Changing embedding model without reindex:** Official docs warn that embedding model/dimension changes require clearing existing data and re-indexing.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Graph + vector RAG storage | Custom graph/vector store | LightRAG default stores | Requirement explicitly mandates LightRAG dual-level graph + vector retrieval. |
| Token chunking and graph extraction | Custom Markdown chunker + entity graph builder | LightRAG insert pipeline | LightRAG handles chunking, entity/relation extraction, merging, status, and persistence. |
| CLI framework | argparse/custom parser | Existing Typer app | Phase 1 already locked Typer behavior and tests. |
| Config precedence | Manual env parsing | Existing `Settings` / `load_settings` | Phase 1 tests lock `.env`, `OOD_` env vars, and explicit override precedence. |
| JSON serialization ad hoc in commands | Per-command dicts with LightRAG internals | OOD output/model layer | Stable automation schema is a phase success criterion. |

**Key insight:** LightRAG solves retrieval architecture, but not the OOD product contract. Hand-roll only the adapter/normalization layer that protects CLI behavior from LightRAG API/storage changes.

## Common Pitfalls

### Pitfall 1: LightRAG Must Be Initialized Explicitly
**What goes wrong:** `AttributeError: __aenter__`, `KeyError: 'history_messages'`, or storage errors.  
**Why it happens:** Official docs require `await rag.initialize_storages()` after construction.  
**How to avoid:** Centralize LightRAG creation in one async context helper and always finalize.  
**Warning signs:** Tests pass only for empty/no-op paths but fail on first real insert/query.

### Pitfall 2: Retrieval-Only Is Not the Same as Full Graph RAG
**What goes wrong:** Missing Cloud LLM credentials make graph extraction/generative answer unavailable.  
**Why it happens:** LightRAG normal indexing relies on LLM for entity/relationship extraction; embeddings are also required.  
**How to avoid:** Plan explicit modes: full `mix` mode with LLM; fallback `naive` vector retrieval with local embeddings and `answer=null`, `llm_used=false`.  
**Warning signs:** No-credential tests unexpectedly make network calls or document indexing marks files failed.

### Pitfall 3: Source Scores Are Not a Stable High-Level Contract
**What goes wrong:** LightRAG structured result includes chunks/references but may not expose a simple per-source score in every mode.  
**Why it happens:** `aquery_data` returns entities/relationships/chunks/references; vector backends return scores internally, but generated references focus on citation.  
**How to avoid:** The OOD adapter should compute a stable relevance score from available vector query results, ordering, and/or returned metadata. Treat score formula as internal but deterministic.  
**Warning signs:** CLI JSON tests assert raw LightRAG fields that disappear or differ between modes.

### Pitfall 4: `reindex` Can Delete Too Much
**What goes wrong:** Clearing `data_dir` removes unrelated runtime files or future manifests.  
**Why it happens:** `data_dir` contains `storage_dir` but may grow in later phases.  
**How to avoid:** Clear only the selected `settings.storage_dir`, recreate it, then index. Never touch `.env` or `knowledge_dir`.  
**Warning signs:** Reindex tests lose files outside `storage_dir`.

### Pitfall 5: Markdown Encoding and Empty Files
**What goes wrong:** Index fails on one odd file or indexes empty documents.  
**Why it happens:** Local Markdown may contain blank files, unusual Unicode, or no frontmatter.  
**How to avoid:** Read as UTF-8, skip empty/whitespace-only docs with a friendly count, do not require frontmatter.  
**Warning signs:** Plain `.md` fixtures fail because metadata is missing.

## Code Examples

Verified patterns from official sources:

### LightRAG Core Initialization and Insert
```python
# Source: https://raw.githubusercontent.com/HKUDS/LightRAG/main/docs/ProgramingWithCore.md
from lightrag import LightRAG, QueryParam

rag = LightRAG(
    working_dir="./rag_storage",
    embedding_func=embedding_func,
    llm_model_func=llm_model_func,
)
await rag.initialize_storages()
await rag.ainsert("Your text")
answer = await rag.aquery("What are the top themes?", param=QueryParam(mode="hybrid"))
await rag.finalize_storages()
```

### Citation-Aware Insert
```python
# Source: LightRAG ProgramingWithCore.md "Citation Functionality"
documents = ["Document content 1", "Document content 2"]
file_paths = ["guide/troubleshooting.md", "tickets/example.md"]
rag.insert(documents, file_paths=file_paths)
```

### Structured Retrieval Without LLM Generation
```python
# Source: LightRAG 1.4.15 lightrag.py `aquery_data` documentation
data = await rag.aquery_data(
    "How do I fix this error?",
    QueryParam(mode="mix", top_k=10, chunk_top_k=10),
)
# data["data"]["chunks"] contains chunk content and file_path; references map IDs to paths.
```

### Stable OOD JSON Shape
```python
# Source: Phase 2 decision D-14/D-15
payload = {
    "query": query,
    "answer": answer if llm_used else None,
    "confidence": confidence.score,
    "confidence_rationale": confidence.rationale,
    "sources": [source.model_dump() for source in sources],
    "llm_used": llm_used,
    "status": "success" if sources else "no_results",
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `hybrid` as default graph query | `mix` integrates KG and vector retrieval and is reranker-friendly | LightRAG docs current in 2026; README notes reranker default direction in 2025-08 | Use `mix` for Phase 2 full mode; keep `naive` for vector-only fallback. |
| Answer-only query APIs | Structured retrieval APIs (`query_data`, `query_llm`, references) | LightRAG README news: 2025-11 API returns retrieved contexts for evaluation | Prefer structured APIs over parsing answer strings. |
| No citation support | `file_paths` and references | LightRAG README news: 2025-03 citation functionality | Insert with relative file paths from the beginning. |
| Stable vector dimension assumed | Embedding model/dimension tied to index | Current docs warn reindex after embedding changes | Store embedding model choice in verbose diagnostics and force reindex after changes. |

**Deprecated/outdated:**
- Relying on `LightRAG.query()` answer string only: insufficient for Phase 2 source/score JSON contract.
- Treating storage artifact filenames as public API: conflicts with D-09.

## Open Questions

1. **Exact local embedding model**
   - What we know: LightRAG recommends mainstream multilingual embeddings such as `BAAI/bge-m3` and `text-embedding-3-large`; no-credential fallback needs local embeddings.
   - What's unclear: Best quality/performance tradeoff for the user's Mac and German/English ticket corpus.
   - Recommendation: Start with sentence-transformers local embeddings and a small multilingual model; make model configurable later, but avoid adding new config surface unless tests need it.

2. **Exact relevance score formula**
   - What we know: Requirement demands source relevance scores; LightRAG structured data may not always expose direct source-level scores.
   - What's unclear: Whether `lightrag-hku 1.4.15` exposes backend scores consistently across `mix` and `naive` modes in installed package internals.
   - Recommendation: Planner should include an adapter spike/test to inspect returned chunk/vector metadata, then normalize to deterministic 0..1 scores. If raw scores are absent, use rank-derived scores initially and document formula.

3. **Cloud LLM provider scope**
   - What we know: Settings support generic `llm_provider`, `llm_model`, and `llm_api_key`; no provider-specific host fields exist yet.
   - What's unclear: Whether Phase 2 should implement only OpenAI-compatible Cloud LLM or multiple providers.
   - Recommendation: Implement one OpenAI-compatible path if credentials exist; otherwise retrieval-only. Avoid broad provider abstraction until required.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| uv | Package management, test commands | ✓ | 0.9.7 | — |
| Python in uv env | Runtime | ✓ | 3.11.14 | — |
| System python3 | Direct shell probes only | ⚠️ | 3.9.6 | Use `uv run python`, not system python. |
| pytest via uv | Test execution | ✓ | 9.0.3 | — |
| ruff via uv | Linting | ✓ | 0.15.12 | — |
| mypy via uv | Type checking | ✓ | 1.20.2 | — |
| lightrag | Phase 2 implementation | ✗ | — | Add `lightrag-hku==1.4.15` via uv. |
| sentence_transformers | Local embedding fallback | ✗ | — | Add `sentence-transformers==5.4.1`, or use provider embeddings only when credentials exist. |
| numpy | Embedding wrappers | ✗ | — | Add dependency with embedding stack. |
| openai | Optional Cloud LLM | ✗ | — | Add only if implementing OpenAI-compatible LLM path. |

**Missing dependencies with no fallback:**
- `lightrag-hku` is required to satisfy RAG-05.

**Missing dependencies with fallback:**
- `openai` is optional; no credentials means retrieval-only.
- `sentence-transformers` can be skipped only if planner accepts no semantic fallback without credentials, but that would conflict with D-05/D-07 intent.

## Validation Architecture

Skipped: `.planning/config.json` has `workflow.nyquist_validation` explicitly set to `false`.

Recommended manual test focus despite skip:
- `uv run pytest tests/test_cli.py tests/test_config.py tests/test_rag.py -q`
- CLI smoke with temp `knowledge/`: `uv run ood index --knowledge-dir <tmp> --storage-dir <tmp>/storage --json`
- Query before index must exit non-zero with instruction to run `ood index`.
- Missing/empty knowledge dir index must exit zero and report zero documents.

## Sources

### Primary (HIGH confidence)
- HKUDS LightRAG README — installation, Core/API distinction, model requirements, storage backends, news on citations/context returns: https://raw.githubusercontent.com/HKUDS/LightRAG/main/README.md
- HKUDS LightRAG `docs/ProgramingWithCore.md` — Core API, initialization, `QueryParam`, insert with `file_paths`, query modes, storage, pitfalls: https://raw.githubusercontent.com/HKUDS/LightRAG/main/docs/ProgramingWithCore.md
- HKUDS LightRAG `docs/LightRAG-API-Server.md` — configuration, references, chunk content, embedding-change warnings, reranking: https://raw.githubusercontent.com/HKUDS/LightRAG/main/docs/LightRAG-API-Server.md
- HKUDS LightRAG source `lightrag/base.py` and `lightrag/lightrag.py` — `QueryParam`, `QueryResult`, `query_data`, `query_llm`, storage lifecycle and file_path fields: https://raw.githubusercontent.com/HKUDS/LightRAG/main/lightrag/base.py and `/lightrag/lightrag.py`
- PyPI JSON API — verified package versions/upload dates for `lightrag-hku`, `sentence-transformers`, `numpy`, `openai`.

### Secondary (MEDIUM confidence)
- Local environment probes via `uv run` for Python, pytest, ruff, mypy versions.
- Project files: `pyproject.toml`, `src/ood/cli.py`, `src/ood/config.py`, `tests/test_cli.py`, `tests/test_config.py`, `.planning/config.json`, `CLAUDE.md`.

### Tertiary (LOW confidence)
- None used for core claims.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — package versions verified from PyPI; LightRAG official docs reviewed.
- Architecture: MEDIUM-HIGH — LightRAG lifecycle/result APIs verified, but exact score extraction needs implementation-time inspection against installed 1.4.15.
- Pitfalls: HIGH — based on official docs/source warnings and project constraints.
- Graceful no-credential fallback: MEDIUM — user decision is clear, but LightRAG's normal graph pipeline is LLM-dependent; fallback design requires careful adapter implementation.

**Research date:** 2026-05-01  
**Valid until:** 2026-05-31 for project architecture; 2026-05-08 for LightRAG API/version details because LightRAG is fast-moving.
