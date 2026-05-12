---
phase: 11-cli-grade-hybrid-retrieval-and-extractive-answer-synthesis
status: planned
created: 2026-05-04
requirements: [RAG-06, ANS-01, GRAPH-01, CLI-01]
depends_on: [10-echtes-lokales-embedding-retrieval-ohne-cloud-llm-aktivieren-und-llm-antwortsynthese-optional-privacy-gated-machen]
---

# Phase 11 Context: CLI-Grade Hybrid Retrieval and Extractive Answer Synthesis

## Objective

Make `ood query` good enough to serve as an AI skill backend before building evaluation gates around it.

The CLI should retrieve with both semantic and lexical signals, produce a local evidence-based answer from top sources, and make the graph-retrieval status explicit.

## Why Now

Phase 10 made local vector retrieval real and Cloud LLM synthesis privacy-gated. The next quality bottleneck is that vector-only retrieval can miss exact IDs, error codes, system names, and short operational ticket terms. Evaluation should measure a CLI path that is already intended to be useful, not a known-incomplete retrieval path.

## Scope

- Add hybrid retrieval: local semantic vectors plus lexical/BM25-style scoring.
- Preserve local-first/no-Cloud behavior by default.
- Build extractive answer synthesis from top sources with evidence snippets and source citations.
- Keep structured ticket intelligence in the output.
- Decide graph retrieval: enable it in the local CLI path or document an explicit defer with activation criteria.
- Preserve JSON output for automation and skill use.

## Out Of Scope

- LLM-as-judge evaluation.
- Cloud LLM answer generation without `OOD_ALLOW_CLOUD_LLM=true`.
- ServiceNow/Jira API integration.
- Hard regression thresholds before a baseline exists.

## Success Criteria

1. `ood query` ranks sources with combined semantic and lexical signals.
2. Exact-match operational tokens can improve ranking even when vector similarity is weak.
3. Query output includes a local extractive answer with cited evidence from top sources.
4. Graph retrieval is either active locally or deliberately deferred with rationale and activation criteria.
5. Human and JSON CLI outputs contain answer, ranked sources, confidence, routing, uncertainties, and retrieval diagnostics.

## Planning Notes

Likely plan split:

1. Hybrid retrieval scoring and diagnostics.
2. Local extractive answer synthesis from top sources.
3. Graph retrieval decision and CLI/docs polish.

After Phase 11 completes, continue with Phase 12 evaluation dataset and deterministic metrics.
