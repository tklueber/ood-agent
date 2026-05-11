# Roadmap: OOD Agent

**Created:** 2026-05-01  
**Updated:** 2026-05-11 after adding Phase 16 operational skill and learning loop
**Granularity:** Coarse  
**Core Value:** Operative Tickets werden durch intelligente Suche über verteilte Wissensquellen schneller gelöst – mit konkreten Handlungsempfehlungen, Quellenbelegen und Routing-Logik.

## Phases

### v1.0 Completed

- [x] **Phase 1: Foundation & CLI** - Python project setup, CLI scaffolding, configuration management
- [x] **Phase 2: Core RAG Engine** - LightRAG integration, indexing, semantic search, source attribution
- [x] **Phase 3: Knowledge Management** - Incremental updates, metadata handling, deduplication
- [x] **Phase 4: Ticket Intelligence** - Intent recognition, routing logic, risk classification

### v1.1 Evaluations- und Real-Data (mockdata-first)

- [x] **Phase 5: Mock Corpus Contract and Safety Foundation** - User can work with a broad, clearly synthetic, safety-validated mock corpus
- [x] **Phase 6: Mock Data Import and Index Validation** - User can prove mock data behaves like normal knowledge through existing index flows

### v1.1 Retrieval Quality Before Evaluation Gates

- [x] **Phase 10: Echtes lokales Embedding-Retrieval ohne Cloud-LLM aktivieren und LLM-Antwortsynthese optional privacy-gated machen** - User can run real local embedding retrieval by default while Cloud LLM answer synthesis remains explicit privacy-approved opt-in behavior
- [x] **Phase 11: CLI-Grade Hybrid Retrieval and Extractive Answer Synthesis** - User can run one CLI query that combines semantic and lexical retrieval, produces local evidence-based answers, and has a clear graph-retrieval decision (completed 2026-05-04)

### v1.1 Evaluation and Feedback Loop

- [x] **Phase 12: Evaluation Dataset and Metric Core** - User can define eval cases and compute deterministic retrieval and ticket-intelligence metrics (completed 2026-05-08)
- [x] **Phase 13: Evaluation Service and CLI Reporting** - User can run black-box evaluations locally and consume human/JSON reports (completed 2026-05-11)
- [x] **Phase 14: Baseline, Feedback Loop, and Review Gate** - User can establish the first baseline and run a reviewed improvement loop before accepting corpus or retrieval changes (completed 2026-05-11)
- [x] **Phase 15: Local Graph-/Metadata Retrieval and Data Quality Review** - User can improve misses like TraceId/Kafka by using local metadata/graph signals and reviewing whether the Obsidian OOD-KB articles are good enough for reliable retrieval (completed 2026-05-08)

### v1.2 Operational Skill and Learning Loop

- [x] **Phase 16: RAG-Backed OOD Skill, LLM Synthesis, and Learning Loop** - User can use an installable OOD incident skill backed by the Python RAG script, privacy-gated LLM synthesis, deterministic forwarding/calendar hand-off, immediate quality feedback, and asynchronous resolution capture (completed 2026-05-11)

## Phase Details

### Phase 1: Foundation & CLI
**Goal**: Developer can run CLI commands with proper Python environment and configuration

**Depends on**: Nothing (first phase)

**Requirements**: INF-05, INF-06, INF-07

**Success Criteria** (what must be TRUE):
  1. Developer can install project dependencies via uv or poetry
  2. CLI provides `index`, `update`, `query`, `reindex` commands (stub implementations)
  3. System loads Cloud LLM credentials from .env file
  4. Index data is persisted outside git repository (./data/ in .gitignore)

**Plans**: 3 plans

Plans:
- [x] 01-foundation-cli-01-PLAN.md — Create uv Python package scaffold, src layout, and safe git/runtime defaults
- [x] 01-foundation-cli-02-PLAN.md — Implement typed configuration loading for paths and Cloud LLM credentials
- [x] 01-foundation-cli-03-PLAN.md — Create Typer CLI command stubs with output modes and config overrides

---

### Phase 2: Core RAG Engine
**Goal**: User can index Markdown files and query them with semantic search

**Depends on**: Phase 1

**Requirements**: RAG-01, RAG-02, RAG-03, RAG-04, RAG-05, INF-01, INF-03, INF-04

**Success Criteria** (what must be TRUE):
  1. User can run `index` command to build knowledge base from knowledge/ directory
  2. User can run `query <text>` and receive relevant results with source attribution
  3. Query results include relevance scores for each source
  4. Query results include confidence scoring for generated answers
  5. System uses LightRAG for dual-level graph + vector retrieval

**Plans**: 4 plans

Plans:
- [x] 02-core-rag-engine-01-PLAN.md — Add LightRAG dependencies and stable RAG result models
- [x] 02-core-rag-engine-02-PLAN.md — Implement Markdown indexing and clean reindex service behavior
- [x] 02-core-rag-engine-03-PLAN.md — Implement semantic query, source scoring, and confidence logic
- [x] 02-core-rag-engine-04-PLAN.md — Wire RAG service into CLI outputs and usage docs

**UI hint**: yes

---

### Phase 3: Knowledge Management
**Goal**: User can update knowledge base incrementally without full rebuilds

**Depends on**: Phase 2

**Requirements**: KNW-01, KNW-02, KNW-03, KNW-04, KNW-05, INF-02

**Success Criteria** (what must be TRUE):
  1. User can run `update` command and only new/changed files are re-indexed
  2. Markdown files contain YAML frontmatter with metadata (Quelle, Datum, Status, System, Komponente)
  3. System detects and reports duplicate knowledge entries during indexing
  4. System maintains file manifest with hash for change detection

**Plans**: 3 plans

Plans:
- [x] 03-01-PLAN.md — Create manifest/update contracts plus frontmatter parsing and metadata validation primitives
- [x] 03-02-PLAN.md — Persist rich manifests during index/reindex and report exact/near duplicates
- [x] 03-03-PLAN.md — Implement incremental `ood update`, CLI diagnostics, and knowledge-management docs

---

### Phase 4: Ticket Intelligence
**Goal**: User receives structured ticket analysis with routing and risk assessment

**Depends on**: Phase 3

**Requirements**: TIC-01, TIC-02, TIC-03, TIC-04, TIC-05

**Success Criteria** (what must be TRUE):
  1. System recognizes ticket intent (Problem / Frage / Request)
  2. Query results include structured answer (Einschätzung, Lösungsweg, Routing, Quellen, Unsicherheiten)
  3. System provides routing logic (selbst lösen / weiterleiten Policen / weiterleiten Offerten / Rückfrage)
  4. System extracts Policennummer and Offertennummer from ticket text
  5. System classifies commands by risk level (grün/gelb/orange/rot)

**Plans**: 3 plans

Plans:
- [x] 04-01-PLAN.md — Create deterministic ticket analysis models and local rule engine
- [x] 04-02-PLAN.md — Wire nested analysis into RagEngine query results
- [x] 04-03-PLAN.md — Render structured ticket intelligence in CLI output and docs

**UI hint**: yes

---

### Phase 5: Mock Corpus Contract and Safety Foundation
**Goal**: User can work with a broad, clearly synthetic, safety-validated mock corpus before any real or anonymized production data is introduced

**Depends on**: Phase 4

**Requirements**: MOCK-01, MOCK-02, MOCK-03, MOCK-05

**Success Criteria** (what must be TRUE):
  1. User can generate or copy an importable Markdown mock corpus covering tickets, Wiki articles, Jira bugs, ServiceNow cases, runbooks, and notes
  2. User can open any mock document and immediately see `mock: true`, dataset metadata, synthetic identifiers, and a visible body warning that it is mock data
  3. User can run a safety validator and see actionable findings for missing mock markers, suspicious real-data patterns, secrets, PII-like content, and golden-answer leakage
  4. User can inspect a corpus coverage summary by source type, system, component, routing target, command-risk level, and scenario category

**Plans**: 3 plans

Plans:
- [x] 05-01-PLAN.md — Create deterministic mock corpus contracts and Markdown generator
- [x] 05-02-PLAN.md — Add mock safety validator and coverage summarizer
- [x] 05-03-PLAN.md — Wire mock corpus generation and validation into CLI/docs

---

### Phase 6: Mock Data Import and Index Validation
**Goal**: User can prove the mock corpus indexes and updates through the existing knowledge flows without special mock-only indexing branches

**Depends on**: Phase 5

**Requirements**: MOCK-04

**Success Criteria** (what must be TRUE):
  1. User can run `ood index` against the mock corpus and see the expected mock Markdown files accepted as normal knowledge documents
  2. User can run `ood reindex` with mock data and verify a clean rebuild uses only the selected mock corpus and fresh storage
  3. User can run `ood update` after adding, changing, or deleting mock files and see manifest-based changed/unchanged/stale diagnostics
  4. User can validate indexing diagnostics without bypassing existing metadata, duplicate, warning, or manifest behavior

**Plans**: 2 plans

Plans:
- [x] 06-01-PLAN.md — Add service-level mock corpus index/reindex validation tests
- [x] 06-02-PLAN.md — Add CLI mock import/update validation tests and README workflow

---

### Phase 7: Evaluation Dataset and Metric Core
**Goal**: User can define versioned evaluation cases and compute deterministic quality metrics for retrieval and ticket intelligence

**Depends on**: Phase 6

**Requirements**: EVAL-01, EVAL-03, EVAL-04

**Success Criteria** (what must be TRUE):
  1. User can author versioned JSON evaluation cases with expected sources, forbidden sources, routing, intent, identifiers, command risks, and uncertainty expectations
  2. User can load an evaluation dataset and receive clear validation errors for malformed cases or references to missing mock sources
  3. User can review retrieval metrics including Hit@1/3/5, MRR, source recall, and forbidden-source rate from deterministic result data
  4. User can review ticket-intelligence metrics for intent, routing, identifier extraction, command-risk classification, and uncertainty behavior

**Plans**: TBD

---

**Superseded by Phase 12 after Phase 11 retrieval-quality insertion. Kept for history.**

---

### Phase 8: Evaluation Service and CLI Reporting
**Goal**: User can run local black-box evaluations through `RagEngine.query()` and consume reports in both human-readable and machine-readable forms

**Depends on**: Phase 7

**Requirements**: EVAL-02, EVAL-06, EVAL-07

**Success Criteria** (what must be TRUE):
  1. User can run an evaluation that calls the public `RagEngine.query()` contract for each case rather than backend internals
  2. User can view concise CLI output that shows run status, core metrics, failed cases, and useful expected-vs-actual diagnostics
  3. User can write structured JSON output containing dataset metadata, case results, metrics, paths, backend information, and `llm_used`
  4. User can run evaluations locally without Cloud LLM usage by default, and every report explicitly shows whether an LLM was used

**Plans**: TBD
**UI hint**: yes

---

**Superseded by Phase 13 after Phase 11 retrieval-quality insertion. Kept for history.**

---

### Phase 9: Baseline, Documentation, and Regression Workflow
**Goal**: User can establish a first observed baseline and repeat the mockdata evaluation workflow without inventing premature hard thresholds

**Depends on**: Phase 8

**Requirements**: EVAL-05

**Success Criteria** (what must be TRUE):
  1. User can run the full v1.1 mock evaluation suite and save a first baseline report with no arbitrary pass/fail threshold required
  2. User can distinguish baseline observations from future regression gates in the report and documentation
  3. User can follow documented commands to regenerate mock data, reindex it, run evaluations, and inspect results locally
  4. User can use documented guidance to add future mock fixtures and evaluation cases without leaking golden answers into indexed Markdown

**Plans**: TBD

---

**Superseded by Phase 14 after Phase 11 retrieval-quality insertion. Kept for history.**

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & CLI | 3/3 | Complete | 2026-05-01 |
| 2. Core RAG Engine | 4/4 | Complete | 2026-05-01 |
| 3. Knowledge Management | 3/3 | Complete | 2026-05-01 |
| 4. Ticket Intelligence | 3/3 | Complete | 2026-05-02 |
| 5. Mock Corpus Contract and Safety Foundation | 3/3 | Complete | 2026-05-03 |
| 6. Mock Data Import and Index Validation | 2/2 | Complete | 2026-05-03 |
| 7. Evaluation Dataset and Metric Core | 0/TBD | Superseded by Phase 12 | - |
| 8. Evaluation Service and CLI Reporting | 0/TBD | Superseded by Phase 13 | - |
| 9. Baseline, Documentation, and Regression Workflow | 0/TBD | Superseded by Phase 14 | - |
| 10. Echtes lokales Embedding-Retrieval ohne Cloud-LLM aktivieren und LLM-Antwortsynthese optional privacy-gated machen | 3/3 | Complete | 2026-05-04 |
| 11. CLI-Grade Hybrid Retrieval and Extractive Answer Synthesis | 3/3 | Complete   | 2026-05-04 |
| 12. Evaluation Dataset and Metric Core | 3/3 | Complete   | 2026-05-08 |
| 13. Evaluation Service and CLI Reporting | 3/3 | Complete    | 2026-05-11 |
| 14. Baseline, Feedback Loop, and Review Gate | 3/3 | Complete    | 2026-05-11 |
| 15. Local Graph-/Metadata Retrieval and Data Quality Review | 5/5 | Complete   | 2026-05-08 |
| 16. RAG-Backed OOD Skill, LLM Synthesis, and Learning Loop | 5/5 | Complete   | 2026-05-11 |

---

## v1.1+v1.2 Requirement Coverage

| Requirement | Phase |
|-------------|-------|
| MOCK-01 | Phase 5 |
| MOCK-02 | Phase 5 |
| MOCK-03 | Phase 5 |
| MOCK-04 | Phase 6 |
| MOCK-05 | Phase 5 |
| RAG-06 | Phase 11 |
| ANS-01 | Phase 11 |
| GRAPH-01 | Phase 11 |
| CLI-01 | Phase 11 |
| EVAL-01 | Phase 12 |
| EVAL-02 | Phase 13 |
| EVAL-03 | Phase 12 |
| EVAL-04 | Phase 12 |
| EVAL-05 | Phase 14 |
| EVAL-06 | Phase 13 |
| EVAL-07 | Phase 13 |
| EVAL-11 | Phase 14 |
| GRAPH-02 | Phase 15 |
| KNW-11 | Phase 15 |
| KNW-12 | Phase 15 |
| SKILL-01 | Phase 16 |
| SKILL-02 | Phase 16 |
| LLM-02 | Phase 16 |
| ROUTE-01 | Phase 16 |
| FB-02 | Phase 16 |
| LEARN-02 | Phase 16 |
| KNW-13 | Phase 16 |

**Coverage:** 27/27 v1.1+v1.2 requirements mapped ✓
**Orphans:** 0  
**Duplicates:** 0

---

## Evolution

This roadmap evolves:
- **After plan completion** (via `/gsd-plan-phase`): Plans column updates
- **After phase completion** (via `/gsd-transition`): Progress table updates, status changes
- **After milestone completion** (via `/gsd-complete-milestone`): Full review, phase additions if scope expands

### Phase 10: Echtes lokales Embedding-Retrieval ohne Cloud-LLM aktivieren und LLM-Antwortsynthese optional privacy-gated machen

**Goal:** User can run real local embedding retrieval by default while Cloud LLM answer synthesis remains explicit privacy-approved opt-in behavior
**Requirements**: LOCAL-RET-01, LOCAL-RET-02, PRIV-01, PRIV-02
**Depends on:** Phase 6
**Plans:** 3/3 plans complete

Plans:
- [x] 10-01-PLAN.md — Add default-deny Cloud LLM privacy approval gate to settings and RagEngine
- [x] 10-02-PLAN.md — Replace lexical fallback with local embedding vector retrieval
- [x] 10-03-PLAN.md — Expose CLI diagnostics and docs for local-first retrieval and opt-in synthesis

---

### Phase 11: CLI-Grade Hybrid Retrieval and Extractive Answer Synthesis

**Goal:** User can run one CLI query that combines semantic and lexical retrieval, produces local evidence-based answers, and has a clear graph-retrieval decision.
**Requirements**: RAG-06, ANS-01, GRAPH-01, CLI-01
**Depends on:** Phase 10
**Plans:** 3/3 plans complete

**Success Criteria** (what must be TRUE):
  1. `ood query` ranks sources with hybrid semantic + lexical/BM25-style scoring and exposes diagnostics for the score components.
  2. Exact identifiers, error codes, system/component names, and ticket terms can lift relevant sources even when vector similarity alone is weak.
  3. Query output includes a local extractive synthesis from top sources with cited evidence snippets and no Cloud LLM dependency.
  4. Graph retrieval is either active in the local CLI query path or consciously deferred with a documented reason, risks, and criteria for activation.
  5. The CLI result is suitable as an AI skill output: answer, ranked sources, confidence, routing, uncertainties, and backend diagnostics are available in human and JSON modes.

Plans:
- [x] 11-01-PLAN.md — Add hybrid semantic+lexical retrieval scoring and query diagnostics
- [x] 11-02-PLAN.md — Build local extractive answer synthesis from top sources
- [x] 11-03-PLAN.md — Expose graph-retrieval defer status and polish CLI/docs diagnostics

---

### Phase 12: Evaluation Dataset and Metric Core

**Goal:** User can define versioned evaluation cases and compute deterministic quality metrics for retrieval and ticket intelligence.
**Requirements**: EVAL-01, EVAL-03, EVAL-04
**Depends on:** Phase 11
**Plans:** 3/3 plans complete

**Success Criteria** (what must be TRUE):
  1. User can load a versioned JSON evaluation dataset with expected sources, forbidden sources, routing, intent, identifiers, command risks, and uncertainty expectations.
  2. Dataset validation reports malformed cases and missing mock source references deterministically before an evaluation run.
  3. User can compute retrieval metrics including Hit@1/3/5, MRR, source recall, and forbidden-source rate from deterministic result data.
  4. User can compute ticket-intelligence metrics for intent, routing, identifier extraction, command-risk classification, and uncertainty behavior from public `TicketAnalysis` output.

Plans:
- [x] 12-01-PLAN.md — Create versioned evaluation dataset contracts and the initial mock-v1 fixture
- [x] 12-02-PLAN.md — Implement deterministic retrieval metrics for ranked source results
- [x] 12-03-PLAN.md — Implement ticket-intelligence metrics and document the Phase 12 metric boundary

---

### Phase 13: Evaluation Service and CLI Reporting

**Goal:** User can run local black-box evaluations through `RagEngine.query()` and consume reports in both human-readable and machine-readable forms.
**Requirements**: EVAL-02, EVAL-06, EVAL-07
**Depends on:** Phase 12
**Plans:** 3/3 plans complete

Plans:
- [x] 13-01-PLAN.md — Build EvalRunner orchestration through RagEngine.query() with credential-only LLM gate, skip/errored handling, and Settings.eval_dataset_path
- [x] 13-02-PLAN.md — Implement JSON report serializer mapping EvalRunResult to the locked schema_version=1 wire schema
- [x] 13-03-PLAN.md — Wire `ood eval run`/`cases` Typer subcommands, German human formatter with »LLM« marker, --dataset/--case-id/--out/--json flags, exit-code policy

---

### Phase 14: Baseline, Feedback Loop, and Review Gate

**Goal:** User can establish a first observed baseline and run reviewed improvement loops without arbitrary premature thresholds.
**Requirements**: EVAL-05, EVAL-11
**Depends on:** Phase 13
**Plans:** 3/3 plans complete

**Success Criteria** (what must be TRUE):
  1. User can save the first baseline report and distinguish observation from pass/fail gating.
  2. Failed evaluation cases produce a review artifact with expected-vs-actual evidence and proposed next action.
  3. Corpus changes, retrieval changes, and baseline updates require an explicit review decision before being accepted as improvements.
  4. Documentation shows the local loop: regenerate mock data, index, query smoke test, evaluate, review, update baseline if approved.

Plans:
- [x] 14-01-PLAN.md — Create pure observational baseline, failed-case review, decision, and gate artifact helpers
- [x] 14-02-PLAN.md — Add `ood eval baseline` and `ood eval review` artifact creation commands
- [x] 14-03-PLAN.md — Add review-decision/update-baseline gate commands and document the local loop

---

### Phase 15: Local Graph-/Metadata Retrieval and Data Quality Review

**Goal:** User can improve operational misses like TraceId/Kafka by combining local graph/metadata retrieval with a concrete quality review of the 438 Obsidian OOD-KB Markdown articles.
**Requirements**: GRAPH-02, KNW-11, KNW-12
**Depends on:** Phase 14
**Plans:** 5/5 plans complete

**Success Criteria** (what must be TRUE):
  1. Local query diagnostics can show when metadata signals, document links, aliases, tags, headings, or explicit entities contributed to ranking, without sending ticket content to a Cloud LLM.
  2. The `/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/articles` corpus is audited for retrieval-readiness across frontmatter completeness, operational keywords, aliases/synonyms, stable titles, headings, cross-links, duplicate/conflicting articles, freshness, and source attribution.
  3. The TraceId/Kafka miss is used as a concrete regression case: `how-to-find-traceid-in-kafka-message.md` should be explainably promoted by metadata/graph signals rather than only appearing at rank 4 through hybrid scoring.
  4. The review produces actionable source-data recommendations such as adding normalized `system`, `component`, `problem_type`, `keywords`, `aliases`, `related`, `supersedes`, `last_verified`, and `owner` metadata where useful; using query-language synonyms like `trace id`, `traceid`, `kafka message`, and `correlation id`; and adding explicit links between troubleshooting articles, tickets, runbooks, and error-code notes.
  5. Implementation remains local-first and privacy-safe: graph/metadata artifacts are derived from Markdown/frontmatter only, remain outside git when generated, and can be evaluated through the Phase 13/14 reporting loop before becoming a default retrieval boost.

Plans:
- [x] 15-01-PLAN.md — Create local graph/metadata artifact contracts and generation during index/update
- [x] 15-02-PLAN.md — Fuse vector, lexical, metadata, and graph signals with TraceId/Kafka regression diagnostics
- [x] 15-03-PLAN.md — Expose graph/metadata fusion diagnostics in CLI output and README workflow
- [x] 15-04-PLAN.md — Build local OOD-KB retrieval-readiness audit and recommendation engine
- [x] 15-05-PLAN.md — Add quality-audit CLI, source-quality guide, and TraceId smoke fixture

---

### Phase 16: RAG-Backed OOD Skill, LLM Synthesis, and Learning Loop

**Goal:** User can operate OOD support through a multi-level skill that uses the Python RAG script as source of truth, handles forwarding and duty calendars before solution work, produces privacy-gated LLM-backed proposals, and learns from immediate plus asynchronous resolution feedback.
**Requirements**: SKILL-01, SKILL-02, LLM-02, ROUTE-01, FB-02, LEARN-02, KNW-13
**Depends on:** Phase 15
**Plans:** 5/5 plans complete

**Success Criteria** (what must be TRUE):
  1. An installable skill generated from the existing `06_OOD-KB/ood-agent` template calls the project RAG CLI/script for retrieval instead of manually reading `_index.md` as the canonical search path.
  2. The skill first runs deterministic routing: recognized forwarding cases return target department/team, assignment hints, and OOD duty person/calendar link; only non-forwarded incidents continue to RAG/LLM solution synthesis.
  3. Privacy-gated LLM synthesis can produce a grounded German solution proposal from retrieved sources while preserving deterministic routing, confidence, source citations, command-risk labels, and uncertainty output.
  4. Every solution response includes an immediate quality-assurance action so the support person can rate usefulness, correctness, routing accuracy, and missing evidence without leaving the flow.
  5. A later actual resolution can be attached to the original query/suggestion, becomes referenceable in evaluation and future answers, and can yield an alternative solution path for similar tickets.
  6. Knowledge maintenance is not manual frontmatter work for the support person: feedback and resolution notes can be transformed into reviewed Markdown/frontmatter updates that encode concepts, regulations, source constraints, ownership, and verification metadata before indexing.

**Planning Notes:**
  1. Preserve the current privacy boundary: deterministic routing and local RAG remain default; Cloud LLM is only used after explicit approval.
  2. Reuse existing calendar/duty-person behavior from the template skill, but move department/routing facts into testable project contracts where feasible.
  3. Treat learning artifacts as review-gated knowledge proposals, not automatic trusted truth, so bad feedback cannot silently poison the KB.

Plans:
- [x] 16-01-PLAN.md — Create deterministic operational routing/calendar hand-off contracts before RAG/LLM synthesis
- [x] 16-02-PLAN.md — Package the installable RAG-backed OOD incident skill and operator guide from the existing template
- [x] 16-03-PLAN.md — Add privacy-gated grounded solution proposal synthesis over QueryResult
- [x] 16-04-PLAN.md — Add immediate feedback, actual-resolution, and pending knowledge-proposal artifact helpers
- [x] 16-05-PLAN.md — Wire the route-first incident CLI plus feedback/resolution/proposal commands and workflow docs

---
*Last updated: 2026-05-11 after adding Phase 16 operational skill and learning loop*
