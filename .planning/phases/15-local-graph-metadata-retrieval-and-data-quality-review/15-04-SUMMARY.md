---
phase: 15-local-graph-metadata-retrieval-and-data-quality-review
plan: 04
subsystem: knowledge-quality
tags: [quality-audit, metadata, recommendations]
requires: []
provides: [audit_knowledge_corpus, KnowledgeQualityReport]
affects: [src/ood/knowledge_quality.py, tests/test_knowledge_quality.py]
tech_stack:
  added: []
  patterns: [stdlib-markdown-frontmatter-audit, dataclass-to-dict]
key_files:
  created: [src/ood/knowledge_quality.py, tests/test_knowledge_quality.py]
  modified: []
decisions:
  - Keep source-data quality audits independent from indexing so the external OOD-KB can be reviewed without Cloud LLM or vector artifacts.
  - Treat recommendations as actionable Markdown edits with document or corpus scope instead of raw metric-only findings.
metrics:
  duration: 14min
  completed: 2026-05-08
  tasks: 2
  files: 2
---

# Phase 15 Plan 04: Knowledge Quality Audit Summary

OOD can now audit a Markdown corpus locally for retrieval-readiness dimensions and emit actionable metadata, link, freshness, source, and TraceId/Kafka recommendations.

## Completed Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1/2 RED | Failing knowledge quality audit tests | 2f3689d | tests/test_knowledge_quality.py |
| 1/2 GREEN | Add knowledge quality audit engine | cd08ba9 | src/ood/knowledge_quality.py |

## What Changed

- Added frozen report dataclasses: `QualityIssue`, `QualityRecommendation`, `FieldCoverage`, and `KnowledgeQualityReport`.
- Added `audit_knowledge_corpus()` with stdlib-only Markdown/frontmatter parsing for metadata coverage, Wikilinks, commands, freshness, duplicates, and source attribution.
- Added recommendation rules for missing normalized fields, sparse links, source attribution, command risk markers, stale verification, and TraceId/Kafka synonym gaps.

## Verification

- `uv run pytest tests/test_knowledge_quality.py -q` → 4 passed.

## Deviations from Plan

None - plan executed as written.

## Known Stubs

None.

## Self-Check: PASSED

- Found summary file: `.planning/phases/15-local-graph-metadata-retrieval-and-data-quality-review/15-04-SUMMARY.md`
- Verified commits exist: 2f3689d, cd08ba9
- Verified key files exist: `src/ood/knowledge_quality.py`, `tests/test_knowledge_quality.py`
