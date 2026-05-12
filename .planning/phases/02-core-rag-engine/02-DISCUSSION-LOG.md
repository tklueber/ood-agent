# Phase 2: Core RAG Engine - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-01
**Phase:** 02-Core RAG Engine
**Areas discussed:** Indexing Behavior, LLM and Privacy Behavior, LightRAG Storage Shape, Query Output Contract

---

## Gray Areas Selected

| Area | Why it mattered | Selected |
|------|-----------------|----------|
| Query output contract | Locks what `ood query` returns in human and `--json` modes: answer vs search results, source fields, scores, confidence. Reuses existing CLI output contract. | yes |
| Indexing behavior | Clarifies what `ood index` and `ood reindex` should do now: source discovery, empty dirs, invalid Markdown, rebuild semantics. Avoids Phase 3 incremental scope. | yes |
| LLM/privacy behavior | Decides whether Phase 2 can call a Cloud LLM, how missing credentials behave, and whether retrieval-only mode is acceptable under data privacy constraints. | yes |
| LightRAG storage shape | Clarifies how strict the user cares about storage location/naming and local artifacts under `data/storage`; code already has configurable `storage_dir`. | yes |

---

## Indexing Behavior

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| How should `ood index` treat the `knowledge/` source set in Phase 2? | Markdown recursive | Index all `*.md` files recursively under `knowledge_dir`; matches Markdown-first scope and common folder exports. | yes |
| How should `ood index` treat the `knowledge/` source set in Phase 2? | Top-level only | Only index Markdown files directly inside `knowledge_dir`; simpler but weak for wiki/Jira export folders. | |
| How should `ood index` treat the `knowledge/` source set in Phase 2? | Configurable glob | Accept a user-specified include pattern now; more flexible but adds CLI/config surface in Phase 2. | |
| What should happen if `knowledge/` is missing or contains no Markdown files? | Friendly no-op | Exit successfully with clear message and zero indexed documents; good local onboarding. | yes |
| What should happen if `knowledge/` is missing or contains no Markdown files? | Fail command | Exit non-zero to force users to provide knowledge before indexing. | |
| What should happen if `knowledge/` is missing or contains no Markdown files? | Create sample | Create example Markdown content; helpful but risks polluting user knowledge. | |
| How strict should Phase 2 be about Markdown content quality? | Accept plain Markdown | Index Markdown body even without frontmatter; Phase 3 handles YAML metadata conventions. | yes |
| How strict should Phase 2 be about Markdown content quality? | Require frontmatter | Fail/skip files without YAML frontmatter now; enforces future convention early but pulls Phase 3 into Phase 2. | |
| How strict should Phase 2 be about Markdown content quality? | Warn on missing metadata | Index plain Markdown but warn when metadata is absent; useful but adds validation behavior. | |
| What should `ood reindex` guarantee? | Clean rebuild | Clear existing LightRAG storage for the selected storage_dir, then rebuild from current Markdown files. | yes |
| What should `ood reindex` guarantee? | Alias index | Treat `reindex` as the same as `index` for now; simpler but less useful. | |
| What should `ood reindex` guarantee? | Prompt before clearing | Ask for confirmation before deleting index data; safer interactively, harder for automation. | |

**User's choice:** Markdown recursive; friendly no-op; accept plain Markdown; clean rebuild.
**Notes:** User chose to move to the next area after these decisions.

---

## LLM and Privacy Behavior

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| Should Phase 2 call the configured Cloud LLM during `ood query`? | Only when configured | Use Cloud LLM if credentials exist; otherwise retrieval-only output. Fits current `has_llm_credentials` behavior and privacy constraint. | yes |
| Should Phase 2 call the configured Cloud LLM during `ood query`? | Require Cloud LLM | Fail `query` without credentials so answers/confidence are always generated, but local testing is harder. | |
| Should Phase 2 call the configured Cloud LLM during `ood query`? | Retrieval-only MVP | Do not call Cloud LLM in Phase 2; return semantic matches only. Conflicts somewhat with confidence scoring requirement. | |
| What may be sent to the Cloud LLM when it is enabled? | Query plus excerpts | Send the user query and short retrieved Markdown excerpts with source identifiers; enough for grounded answer generation. | |
| What may be sent to the Cloud LLM when it is enabled? | Query only | Never send knowledge content; safer but prevents source-grounded generated answers. | |
| What may be sent to the Cloud LLM when it is enabled? | Full source docs | Send whole matched documents; more context but higher privacy and token risk. | yes |
| How should missing LLM credentials affect `ood query`? | Degrade gracefully | Return ranked sources and state that generated answer/confidence are unavailable without credentials. | yes |
| How should missing LLM credentials affect `ood query`? | Fail with setup hint | Exit non-zero and tell user which `OOD_` variables to configure. | |
| How should missing LLM credentials affect `ood query`? | Use fake answer | Generate placeholder/stub answer for local demo; risks misleading output. | |
| How should Phase 2 express answer confidence? | Heuristic confidence | Use retrieval score spread/source count and LLM availability to produce low/medium/high or numeric confidence; enough for MVP. | yes |
| How should Phase 2 express answer confidence? | LLM self-rating | Ask the Cloud LLM to rate confidence; simple but less deterministic. | |
| How should Phase 2 express answer confidence? | Raw scores only | Expose source relevance only and defer answer confidence despite RAG-04; may under-satisfy requirement. | |

**User's choice:** Cloud LLM only when configured; full source docs may be sent; missing credentials degrade gracefully; confidence is heuristic.
**Notes:** User chose to move to the next area after these decisions.

---

## LightRAG Storage Shape

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| How visible should LightRAG's storage internals be to the user? | Opaque internals | Use `storage_dir` as an implementation-owned directory; users only care that it persists outside git. | yes |
| How visible should LightRAG's storage internals be to the user? | Documented structure | Define subdirectory names and artifact types now; useful for debugging but couples users to internals. | |
| How visible should LightRAG's storage internals be to the user? | User-managed files | Expose index artifact paths as part of the CLI contract; flexible but brittle. | |
| Where should Phase 2 store LightRAG artifacts by default? | data/storage | Use the already-established `settings.storage_dir`; matches Phase 1 config and gitignore contract. | yes |
| Where should Phase 2 store LightRAG artifacts by default? | data/lightrag | More explicit LightRAG naming, but changes the existing derived default. | |
| Where should Phase 2 store LightRAG artifacts by default? | data/index | Generic name if LightRAG may be swapped later, but less aligned with current config naming. | |
| How should `index` behave when storage already exists? | Reuse/update best effort | Let LightRAG add documents if possible; full clean rebuild remains `reindex`. Avoids accidental data deletion. | yes |
| How should `index` behave when storage already exists? | Fail and suggest reindex | Avoids duplicate/ambiguous index state but makes normal use clunkier. | |
| How should `index` behave when storage already exists? | Always clear first | Simple deterministic behavior but duplicates `reindex` and risks deleting user data. | |
| Should Phase 2 expose storage diagnostics in CLI output? | Verbose only | Show storage path/document counts under `--verbose` or `--json`; keep normal output concise. | yes |
| Should Phase 2 expose storage diagnostics in CLI output? | Always show | Transparent for users, but noisy for normal queries/indexing. | |
| Should Phase 2 expose storage diagnostics in CLI output? | Never show | Clean UX, but harder to debug local indexing issues. | |

**User's choice:** Opaque internals; default `data/storage`; reuse/update best effort for `index`; storage diagnostics only in verbose/JSON output.
**Notes:** User chose to move to the next area after these decisions.

---

## Query Output Contract

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| What should `ood query <text>` return by default in human mode? | Answer plus sources | Show concise generated answer when LLM is available, then ranked sources with scores; retrieval-only shows sources and no-answer note. | |
| What should `ood query <text>` return by default in human mode? | Sources only | Always return ranked matches only; simpler, but less aligned with answer/confidence requirement. | |
| What should `ood query <text>` return by default in human mode? | Verbose analysis | Show answer, sources, confidence rationale, and excerpts by default; rich but potentially noisy. | yes |
| What fields must `--json` include for query results? | Stable full schema | Include query, answer/null, confidence, sources[{path, score, excerpt}], llm_used, status; good for automation/tests. | yes |
| What fields must `--json` include for query results? | Minimal schema | Only include answer and sources; faster to implement but weaker contract. | |
| What fields must `--json` include for query results? | Mirror LightRAG raw | Expose whatever LightRAG returns; less work, but unstable for downstream users. | |
| How should source attribution identify documents? | Relative path plus excerpt | Use path relative to `knowledge_dir`, score, and short excerpt/snippet; directly useful to users. | yes |
| How should source attribution identify documents? | Filename only | Cleaner output but ambiguous for nested knowledge folders. | |
| How should source attribution identify documents? | Absolute path | Precise locally but noisy and less portable in JSON/logs. | |
| How should `ood query` behave when no index exists yet? | Fail with index hint | Exit non-zero with clear instruction to run `ood index`; prevents false empty results. | yes |
| How should `ood query` behave when no index exists yet? | Auto-index first | Convenient but query command becomes slow/destructive and hides indexing errors. | |
| How should `ood query` behave when no index exists yet? | Return empty results | Simple but confusing; looks like no relevant knowledge exists. | |

**User's choice:** Human mode should show verbose analysis; JSON should use stable full schema; sources use relative paths plus excerpts; missing index fails with an `ood index` hint.
**Notes:** User chose to move to the next area after these decisions.

---

## Final Confirmation

The user confirmed readiness to create context after reviewing the captured summary.

## the agent's Discretion

- Exact LightRAG adapter structure, embedding/LLM provider integration details, prompt wording, confidence formula, excerpt length, and Rich formatting remain implementation details for research/planning.

## Deferred Ideas

None.
