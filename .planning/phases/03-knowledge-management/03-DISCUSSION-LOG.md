# Phase 3: Knowledge Management - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-05-01
**Phase:** 03-knowledge-management
**Areas discussed:** Update behavior, Metadata rules, Duplicate handling, Manifest contract

---

## Area Selection

| Option | Description | Selected |
|--------|-------------|----------|
| Update behavior | Lock how `ood update` handles new, changed, unchanged, and deleted Markdown files; CLI stub and RagEngine indexing path already exist. | yes |
| Metadata rules | Decide required YAML frontmatter behavior: strict vs warning-only, allowed status/source fields, and how metadata affects indexing. | yes |
| Duplicate handling | Decide exact vs near-duplicate detection and whether duplicates are skipped, reported, or indexed with warnings. | yes |
| Manifest contract | Decide manifest location/shape and what details JSON/human output must expose for downstream automation. | yes |

**User's choice:** Discuss all proposed gray areas.
**Notes:** Prior decisions already locked CLI shape, JSON/human output modes, safe storage, and Cloud-LLM privacy behavior.

---

## Update Behavior

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| Changed file handling | Changed/new only | Manifest hash decides what needs indexing; unchanged files are skipped. | yes |
| Changed file handling | Refresh affected docs | Also clean or replace prior records for changed paths if supported. | no |
| Changed file handling | Always batch rebuild | Treat update as a safer mini-reindex. | no |
| Deleted files | Report stale entries | Detect and report deleted paths, but do not mutate LightRAG internals unless safe support exists. | yes |
| Deleted files | Remove from index | Attempt to delete removed files from retrieval storage during update. | no |
| Deleted files | Ignore deletions | Only process current files; cleanup remains `ood reindex` responsibility. | no |
| No changes | Success no-op | Exit 0 with clear message and JSON counts all zero. | yes |
| No changes | Warn no-op | Exit 0 but treat as a warning in human output. | no |
| No changes | Fail no-op | Exit non-zero to signal automation that no update work happened. | no |
| First run | Bootstrap allowed | If no manifest exists, behave like first incremental build and create it. | yes |
| First run | Require index first | Force users to run `ood index` or `ood reindex` before update. | no |
| First run | You decide | Leave behavior to planning. | no |

**User's choice:** Changed/new only; report stale deleted paths; success no-op; bootstrap allowed.
**Notes:** User chose to move to the next area after these decisions.

---

## Metadata Rules

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| Validation strictness | Warn and skip invalid | Valid docs index; invalid/missing metadata is reported and skipped. | no |
| Validation strictness | Warn but index | Index documents even when metadata is missing or invalid. | yes |
| Validation strictness | Fail command | Any invalid metadata fails the whole command. | no |
| Required fields | Five roadmap fields | Require `quelle`, `datum`, `status`, `system`, `komponente`. | no |
| Required fields | Add title/type | Require roadmap fields plus `title` and `type`. | yes |
| Required fields | Minimal required | Require only `quelle`, `datum`, and `status`. | no |
| Status values | active/deprecated/draft | Simple lifecycle enough for freshness warnings without full API lifecycle scope. | yes |
| Status values | valid/outdated/draft | More explicit support for outdated knowledge entries. | no |
| Status values | Free text | Accept any non-empty status. | no |
| Indexed text | Strip frontmatter | Index clean Markdown body and store metadata separately. | yes |
| Indexed text | Include frontmatter | Metadata terms become searchable but may pollute excerpts and answers. | no |
| Indexed text | You decide | Leave to researcher/planner. | no |

**User's choice:** Warn but index; require `quelle`, `datum`, `status`, `system`, `komponente`, `title`, and `type`; recognize `active`, `deprecated`, and `draft`; strip frontmatter from retrieval text.
**Notes:** User chose to move to the next area after these decisions.

---

## Duplicate Handling

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| Detection level | Exact content first | Hash normalized Markdown body for reliable MVP duplicate detection. | no |
| Detection level | Exact plus near | Also flag near-duplicates using text similarity. | yes |
| Detection level | Metadata identity | Treat same title/system/component as potential duplicate regardless of content. | no |
| Duplicate action | Report and index | Surface duplicate warnings but keep all documents searchable. | yes |
| Duplicate action | Report and skip dupes | Index the first document only, skip duplicate copies. | no |
| Duplicate action | Fail command | Block indexing/update until duplicates are resolved. | no |
| Canonical document | Newest active date | Prefer `status=active`, then newest `datum`, then deterministic path order. | yes |
| Canonical document | First path order | Sorted path order wins. | no |
| Canonical document | No primary | Report all members as equivalent. | no |
| Detection scope | Whole directory | Compare against full manifest/current corpus. | no |
| Detection scope | Touched files only | Fastest update behavior; duplicates among unchanged files are ignored until reindex. | yes |
| Detection scope | You decide | Leave exact comparison set to planning. | no |
| Touched comparison | Compare to existing | Touched files trigger checks, but each touched file is compared against current corpus/manifest. | yes |
| Touched comparison | Touched vs touched only | Only compare new/changed files with each other during update. | no |
| Touched comparison | You decide | Leave exact comparison set to planning. | no |

**User's choice:** Exact plus near-duplicate detection; report and index; canonical by active/newest date; update checks touched files against existing corpus.
**Notes:** A follow-up clarified that touched files should still be compared against unchanged existing files. User then chose to move to the next area.

---

## Manifest Contract

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| Location | storage dir JSON | Store `manifest.json` under configured `storage_dir`, alongside retrieval artifacts and outside git. | yes |
| Location | data dir JSON | Store `data/manifest.json` separately from LightRAG artifacts. | no |
| Location | knowledge dir file | Keep manifest near source docs; risks committing runtime state. | no |
| Entry shape | Path hash metadata | Relative path, content hash, normalized body hash, metadata, indexed timestamp, warnings. | no |
| Entry shape | Path hash only | Minimal change detection. | no |
| Entry shape | Full document cache | Store path, hashes, metadata, body text/excerpt, and duplicate details. | yes |
| JSON output | Counts and paths | Counts plus arrays for indexed, skipped, stale/deleted, metadata warnings, duplicate warnings. | no |
| JSON output | Counts only | Stable minimal schema with no long file lists. | no |
| JSON output | Full diagnostics | Include detailed manifest diff and duplicate groups in JSON output. | yes |
| Versioning | Version and rebuild | Include schema_version; incompatible versions ask for rebuild/bootstrap. | yes |
| Versioning | Best effort migrate | Try to migrate old manifests automatically. | no |
| Versioning | No versioning | Keep implementation simpler during MVP. | no |

**User's choice:** Store manifest JSON under `storage_dir`; cache full document data; expose full diagnostics in JSON; version schema and require rebuild/bootstrap for incompatible versions.
**Notes:** User chose to create context after these decisions.

---

## the agent's Discretion

- Exact near-duplicate threshold and similarity algorithm.
- Exact manifest filename and JSON field ordering.
- Exact date parsing/normalization for `datum`.
- Exact human-output wording within existing CLI conventions.

## Deferred Ideas

None - discussion stayed within phase scope.
