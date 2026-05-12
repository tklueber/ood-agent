---
phase: 15-local-graph-metadata-retrieval-and-data-quality-review
plan: 05
subsystem: cli-docs-quality
tags: [quality-audit, docs, evaluation-fixture]
requires: [15-03, 15-04]
provides: [quality-audit-cli, ood-kb-source-quality-guide, ood-kb-traceid-smoke]
affects: [src/ood/cli.py, tests/test_cli.py, README.md, docs/ood-kb-source-quality.md, evaluation/datasets/ood-kb-traceid-smoke.json]
tech_stack:
  added: []
  patterns: [local-json-report, external-corpus-smoke-fixture]
key_files:
  created: [docs/ood-kb-source-quality.md, evaluation/datasets/ood-kb-traceid-smoke.json]
  modified: [src/ood/cli.py, tests/test_cli.py, README.md]
decisions:
  - Write quality-audit reports only when users provide --report-path and keep recommended report paths under ignored data/.
  - Treat the TraceId/Kafka smoke fixture as an external OOD-KB case, not part of the synthetic mock corpus.
metrics:
  duration: 16min
  completed: 2026-05-08
  tasks: 2
  files: 5
---

# Phase 15 Plan 05: Quality CLI, Source Guide, and TraceId Fixture Summary

The quality review is now runnable from the CLI, documented for the 438-document OOD-KB corpus, and backed by a portable TraceId/Kafka smoke fixture.

## Completed Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 RED | Failing quality audit CLI tests | 2fcf867 | tests/test_cli.py |
| 1 GREEN | Add local quality audit CLI | 452e12c | src/ood/cli.py |
| 2 | Add source-quality guide and TraceId fixture | 1fbed7f | README.md, docs/ood-kb-source-quality.md, evaluation/datasets/ood-kb-traceid-smoke.json |

## What Changed

- Added `ood quality-audit` with `--corpus-dir`, `--expected-documents`, `--report-path`, `--json`, `--quiet`, and `--verbose`.
- Added source-quality guidance for normalized metadata, TraceId/Kafka synonyms, Wikilinks, command risk markers, title quality, freshness, ownership, and source attribution.
- Added `evaluation/datasets/ood-kb-traceid-smoke.json` with query `TraceId Kafka AKHQ Ersatzgeschäft` and expected source `how-to-find-traceid-in-kafka-message.md`.
- Updated README with quality-audit, report, reindex, query, and future Phase 13/14 fixture workflow notes.

## Verification

- `uv run pytest tests/test_cli.py tests/test_knowledge_quality.py tests/test_rag.py tests/test_models.py -q` → 72 passed.
- `uv run ood quality-audit --corpus-dir /Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/articles --expected-documents 438 --report-path data/reports/ood-kb-quality.json --json` → document_count 438, expected_document_mismatch false, readiness_score 0.2038. Generated report remained under ignored `data/`.

## Deviations from Plan

None - plan executed as written.

## Known Stubs

None.

## Self-Check: PASSED

- Found summary file: `.planning/phases/15-local-graph-metadata-retrieval-and-data-quality-review/15-05-SUMMARY.md`
- Verified commits exist: 2fcf867, 452e12c, 1fbed7f
- Verified key files exist: `src/ood/cli.py`, `tests/test_cli.py`, `README.md`, `docs/ood-kb-source-quality.md`, `evaluation/datasets/ood-kb-traceid-smoke.json`
