# Phase 15 Discovery: Local Graph/Metadata Retrieval and OOD-KB Quality Review

**Phase:** 15-local-graph-metadata-retrieval-and-data-quality-review  
**Date:** 2026-05-08  
**Discovery level:** Level 2 — new local graph/metadata retrieval path plus source-data quality assessment  
**Privacy stance:** local-only; no Cloud LLM dependency or content-send path

## Inputs Reviewed

- `.planning/ROADMAP.md` Phase 15 goal, requirements, and success criteria.
- `.planning/REQUIREMENTS.md` requirements `GRAPH-02`, `KNW-11`, `KNW-12`.
- Phase 11 summaries: hybrid semantic+lexical retrieval, local extractive answer synthesis, explicit graph defer status.
- Phase 12 summaries: evaluation data/metric boundary and black-box `SourceHit` comparison patterns.
- Current implementation contracts in `src/ood/models.py`, `src/ood/rag.py`, `src/ood/cli.py`, and tests.
- Obsidian OOD-KB sample corpus at `/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/articles`.

## Observed Corpus Signals

- The target corpus contains 438 indexed Markdown articles per user-provided context.
- The regression target file `how-to-find-traceid-in-kafka-message.md` has strong frontmatter signals:
  - `title: "How-To Find TraceId in Kafka Message"`
  - `type: how-to`
  - `service: Kafka`
  - `keywords_de`: `TraceId`, `Kafka`, `AKHQ`, `Ersatzgeschäft`, `Splunk`, `Header`, `Topic`, `Logs`, `Fehlersuche`, `Message`
  - `keywords_en`: `TraceId`, `Kafka`, `AKHQ`, `replacement-business`, `Splunk`, `header`, `topic`, `logs`, `troubleshooting`, `message`
  - body mentions `CREATE_ERSATZGESCHAEFT`, AKHQ topic navigation, Headers, Trace Id, and Splunk query.
  - Wikilinks to `how-to-splunk`, `how-to-signalfx-apm`, `ersatzgeschaft-nicht-moglich`, `reprocessing-domain-commands`, and `how-to-signalfx-metrics`.
- Related articles such as `uno-fehler-offerte-verarbeitung.md`, `how-to-splunk.md`, `how-to-signalfx-apm.md`, `how-to-retry-neu-auslosen.md`, and `reprocessing-domain-commands.md` link to `how-to-find-traceid-in-kafka-message.md`, making incoming-link graph centrality useful for operational queries.
- Current Phase 3 indexing strips frontmatter before local vector indexing. That explains why frontmatter-only keywords/service/type can fail to lift the right article.
- Current Phase 11 diagnostics expose semantic and lexical components, but graph is only `deferred`; they do not explain metadata, link, heading, alias, command, or final-fusion contributions.

## Current Code Constraints

- `QueryResult` already carries `retrieval_diagnostics`; additive fields preserve JSON compatibility if default factories and `to_dict()` remain stable.
- Local fallback artifact is `ood-local-vector-index.json`; generated artifacts must stay under `storage_dir` and outside git.
- Existing YAML frontmatter parser is dependency-free and scalar-oriented. Phase 15 should keep stdlib parsing and add minimal list-field support for OOD-KB fields rather than adding PyYAML.
- CLI output should remain thin and read from public model contracts; JSON output should remain exactly `QueryResult.to_dict()` or command result `to_dict()` payloads.
- Tests should monkeypatch embeddings to avoid model downloads.

## Planning Decisions

1. Implement a deterministic local graph/metadata artifact (`ood-local-graph-index.json`) generated from Markdown/frontmatter/headings/Wikilinks/commands alongside the vector artifact.
2. Extend retrieval diagnostics to show separate vector/semantic, lexical, metadata, graph, and final fusion values for every ranked source.
3. Keep all scoring local and explainable. No Cloud LLM, no external API, and no secrets in artifacts.
4. Add a source-data quality audit as a first-class local module and CLI report, not as manual spreadsheet work.
5. Treat the TraceId/Kafka miss as a regression case that must prove `how-to-find-traceid-in-kafka-message.md` is promoted by metadata/graph signals.
6. Generate actionable source-data recommendations, including normalized fields (`system`, `component`, `problem_type`, `keywords`, `aliases`, `related`, `supersedes`, `last_verified`, `owner`) and query-language synonyms (`trace id`, `traceid`, `kafka message`, `correlation id`).

## Risks and Mitigations

- **Risk:** naive metadata boosts could over-promote broad articles.  
  **Mitigation:** weight metadata/graph modestly, require per-source diagnostics, and evaluate through Phase 13/14 before making boosts irreversible.
- **Risk:** frontmatter list parsing may be incomplete.  
  **Mitigation:** support the observed indented `key:\n  - value` shape and preserve unknown fields as strings/lists for diagnostics.
- **Risk:** real OOD-KB corpus lives outside the repo.  
  **Mitigation:** tests use synthetic fixtures; docs/CLI commands point to the external path without committing generated reports.
- **Risk:** generated graph/quality artifacts may include source content.  
  **Mitigation:** store them only under `storage_dir`, keep summaries concise, and never commit runtime artifacts.
