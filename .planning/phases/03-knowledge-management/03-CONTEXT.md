# Phase 3: Knowledge Management - Context

**Gathered:** 2026-05-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 turns the existing Markdown indexing foundation into maintainable knowledge-base operations. Users can run `ood update` to process new and changed Markdown files without a full rebuild, validate YAML frontmatter conventions, detect duplicate knowledge entries, and maintain a manifest for hash-based change detection.

**In scope:** Incremental update behavior, file manifest, YAML frontmatter metadata checks, duplicate and near-duplicate reporting, and CLI/JSON output contracts for `update` plus affected indexing flows.

**Out of scope:** Ticket intent/routing, command risk classification, Knowledge API lifecycle, automatic ServiceNow/Jira ingestion, web UI, Teams integration, and automatic resolution of stale/conflicting knowledge beyond reporting.

</domain>

<decisions>
## Implementation Decisions

### Update Behavior
- **D-01:** `ood update` should use manifest hashes to process only new and changed Markdown files. Unchanged files are skipped.
- **D-02:** Deleted files from `knowledge/` should be detected and reported as stale entries, but Phase 3 should not mutate LightRAG internals to delete them unless research confirms a safe supported path. Cleanup remains possible through `ood reindex`.
- **D-03:** If no files changed, `ood update` exits successfully as a no-op with a clear human message and zeroed JSON counts.
- **D-04:** `ood update` may bootstrap on first run when no manifest exists, creating the manifest rather than requiring a prior `ood index` or `ood reindex`.

### Metadata Rules
- **D-05:** YAML frontmatter validation should be warning-based: missing or invalid metadata is reported, but documents are still indexed.
- **D-06:** Required frontmatter fields are `quelle`, `datum`, `status`, `system`, `komponente`, `title`, and `type`.
- **D-07:** Recognized `status` values are `active`, `deprecated`, and `draft`.
- **D-08:** Frontmatter should be stripped from text sent to LightRAG/retrieval. Metadata should be stored separately for manifest, warnings, reporting, and future filtering.

### Duplicate Handling
- **D-09:** Phase 3 should detect both exact duplicates and near-duplicates.
- **D-10:** Duplicate findings are reported but do not block indexing/update and do not cause duplicate documents to be skipped.
- **D-11:** Duplicate groups should identify a canonical/primary document for reporting by preferring `status=active`, then newest `datum`, then deterministic path order.
- **D-12:** During `ood update`, duplicate detection should be triggered only by touched files, but each touched file should be compared against the existing corpus/manifest so new duplicates of unchanged documents are still reported. Full unchanged-vs-unchanged duplicate cleanup can wait for `ood reindex` or later maintenance.

### Manifest Contract
- **D-13:** The manifest should be stored as JSON under the configured `storage_dir`, alongside retrieval artifacts and outside git.
- **D-14:** Each manifest entry should cache full document-level data needed for diagnostics: relative path, content hash, normalized body hash, parsed metadata, indexed timestamp, warnings, body text or excerpt, and duplicate details where available.
- **D-15:** `ood update --json` should expose full diagnostics, including manifest diff details, duplicate groups, metadata warnings, stale/deleted paths, indexed paths, skipped paths, and counts.
- **D-16:** The manifest must include a `schema_version`. If an incompatible manifest schema is encountered, the command should instruct the user to rebuild/bootstrap rather than attempting a best-effort migration in Phase 3.

### the agent's Discretion
- Exact near-duplicate algorithm and threshold, as long as exact duplicates are reliable and near-duplicates are reported with useful context.
- Exact manifest filename under `storage_dir` and JSON field ordering.
- Exact date parsing/normalization for `datum`, as long as canonical selection can prefer newest active documents.
- Exact human-output wording, provided it stays consistent with existing `--json`, `--verbose`, and `--quiet` CLI conventions.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Scope and Requirements
- `.planning/ROADMAP.md` §Phase 3: Knowledge Management - Defines the fixed phase goal, dependency on Phase 2, success criteria, and mapped requirements.
- `.planning/REQUIREMENTS.md` §Knowledge Management and §Infrastructure - Defines KNW-01 through KNW-05 and INF-02 for incremental updates, metadata, duplicates, frontmatter convention, and manifest tracking.
- `.planning/PROJECT.md` §Constraints and §Context - Defines Markdown as canonical knowledge format, local MVP, privacy constraints, and CLI-first architecture.
- `.planning/STATE.md` §Current Position - Captures the current focus and success criteria for Phase 3.

### Prior Decisions
- `.planning/phases/01-foundation-cli/01-CONTEXT.md` - Locks uv/Python 3.10+, Typer CLI, flat `index`/`update`/`query`/`reindex` commands, config precedence, `knowledge/`, `data/`, `data/storage`, and CLI output modes.
- `.planning/phases/02-core-rag-engine/02-CONTEXT.md` - Locks recursive Markdown indexing, forgiving empty/missing knowledge directory behavior, `reindex` as the explicit clean rebuild, storage-dir opacity, retrieval-only fallback, and stable query/index result contracts.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/ood/cli.py` - Existing Typer app already exposes `update` as a stub with the same shared options as `index`, `query`, and `reindex`; Phase 3 should replace the stub while preserving command shape.
- `src/ood/rag.py` - `RagEngine` already owns Markdown discovery, document loading, indexing, reindex cleanup, local fallback index writing, and query behavior. Incremental update and manifest logic should integrate here or in a small service behind it.
- `src/ood/models.py` - `IndexResult`, `QueryResult`, `SourceHit`, and `ConfidenceScore` establish frozen dataclass result contracts with `to_dict()` serialization. Phase 3 will likely need to extend or add result models for update diagnostics.
- `tests/test_cli.py` - Current tests assert update stub behavior, shared path overrides, JSON output, verbose/quiet modes, and query/index contracts.
- `tests/test_rag.py` - Current tests lock recursive Markdown discovery, no-op empty indexing, clean reindex behavior, non-clearing index behavior, fallback index behavior, and source path normalization.

### Established Patterns
- CLI commands load `Settings`, instantiate `RagEngine`, and keep output rendering thin.
- Human output is friendly by default; `--json` is machine-readable; `--verbose` adds diagnostics; `--quiet` suppresses non-essential output.
- Runtime data and retrieval artifacts live under configurable local paths outside git.
- `ood reindex` is the explicit destructive rebuild path; normal `index` does not clear existing storage.
- Missing LLM credentials must remain safe and local; Phase 3 metadata/manifest behavior should not introduce Cloud LLM calls.

### Integration Points
- `ood update` in `src/ood/cli.py` should call a real RagEngine/service method and emit a stable update result instead of `_emit_stub`.
- Markdown parsing currently happens in `RagEngine._load_markdown_documents()`; Phase 3 can extend this path to parse frontmatter, strip it from indexed body text, compute hashes, and collect warnings.
- The existing local fallback index file `ood-fallback-index.json` under `storage_dir` suggests `storage_dir` is already the right home for additional runtime JSON such as the manifest.

</code_context>

<specifics>
## Specific Ideas

- The project should stay forgiving for the local MVP: metadata issues and duplicate findings should warn/report, not block indexing.
- The update path should be truly incremental for normal use, while `reindex` remains the reliable full rebuild and cleanup command.
- The manifest is not just a minimal hash map; it should support rich diagnostics for automation and future planning.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 03-knowledge-management*
*Context gathered: 2026-05-01*
