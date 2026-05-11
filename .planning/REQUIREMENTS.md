# Requirements: OOD Agent v1.1+v1.2

**Defined:** 2026-05-02  
**Updated:** 2026-05-11 for RAG-backed operational skill, LLM synthesis, and learning loop
**Milestone:** v1.2 Operational Skill and Learning Loop  
**Core Value:** Operative Tickets werden durch intelligente Suche ueber verteilte Wissensquellen schneller geloest - mit konkreten Handlungsempfehlungen, Quellenbelegen und Routing-Logik.

## v1.1 Requirements

Requirements fuer den naechsten Milestone. Fokus: umfangreiche Mockdaten, sichere Kennzeichnung, Import-/Index-Validierung und reproduzierbare Evaluation.

### Mock Corpus and Safety

- [x] **MOCK-01**: User can generate or use an extensive importable mock Markdown corpus covering tickets, Wiki articles, Jira bugs, ServiceNow cases, runbooks, and notes
- [x] **MOCK-02**: User can distinguish every mock document from real data through mandatory `mock: true`, dataset metadata, synthetic identifiers, and visible body warnings
- [x] **MOCK-03**: User can run a mock-data safety validator that flags missing mock markers, suspicious real-data patterns, secrets, PII-like content, and golden-answer leakage
- [x] **MOCK-04**: User can validate mock data through existing `index`, `reindex`, and `update` flows without special indexing branches
- [x] **MOCK-05**: User can inspect corpus coverage by source type, system, component, routing target, command-risk level, and scenario category

### CLI-Grade Retrieval and Local Answer Quality

- [x] **RAG-06**: User can query with hybrid retrieval that combines local semantic vectors and lexical/BM25-style exact-match signals for IDs, error codes, systems, and key ticket terms
- [x] **ANS-01**: User receives a local, extractive answer synthesis from top sources that cites evidence and works without Cloud LLM approval
- [x] **GRAPH-01**: User has either a real local graph-retrieval path enabled for CLI queries or an explicit documented defer decision with rationale and replacement criteria
- [x] **CLI-01**: User can run one CLI command and get a skill-usable result containing answer, ranked sources, confidence, routing, uncertainty, and diagnostics

### Evaluation Dataset, Metrics, and Feedback Loop

- [x] **EVAL-01**: User can define versioned JSON evaluation cases with expected sources, forbidden sources, routing, intent, identifiers, command risks, and uncertainty expectations
- [x] **EVAL-02**: User can run evaluations through the public `RagEngine.query()` contract so retrieval backends stay black-box interchangeable
- [x] **EVAL-03**: User can review retrieval metrics including Hit@1/3/5, MRR, source recall, and forbidden-source rate
- [x] **EVAL-04**: User can review ticket-intelligence metrics for intent, routing, identifier extraction, command-risk classification, and uncertainty behavior
- [x] **EVAL-05**: User can establish a first baseline report without arbitrary hard thresholds before representative mock data exists
- [x] **EVAL-06**: User can consume evaluation results in both concise human-readable CLI output and structured JSON output
- [x] **EVAL-07**: User can run evaluation locally without Cloud LLM usage by default, with every report explicitly showing `llm_used`
- [x] **EVAL-11**: User can use a feedback loop with a review gate that records failed cases, proposed corpus/query fixes, reviewer decision, and baseline update status

### Local Graph/Metadata Retrieval and Knowledge Quality

- [x] **GRAPH-02**: User can use local metadata and graph-derived signals from Markdown/frontmatter, headings, aliases, tags, and links to improve ranking for operational queries without Cloud LLM usage
- [x] **KNW-11**: User can audit the 438-document Obsidian OOD-KB article corpus for retrieval readiness, including metadata completeness, operational keywords, aliases, cross-links, duplicates/conflicts, freshness, and source attribution
- [x] **KNW-12**: User receives actionable source-data improvement recommendations that make relevant articles easier to retrieve, including normalized fields, query-language synonyms, related-article links, ownership, and last-verified metadata

## v1.2 Requirements

Requirements fuer den naechsten Nutzbarkeits-Meilenstein. Fokus: ein mehrstufiger OOD-Skill, der das lokale RAG per Script als Quelle nutzt, privacy-gated LLM-Antworten erzeugt, Weiterleitungen mit OOD-Diensthabenden abbildet und aus Support-Feedback lernt.

### RAG-Backed OOD Skill and LLM Synthesis

- [x] **SKILL-01**: User can invoke an installable OOD incident skill derived from the existing `06_OOD-KB/ood-agent` template, with the Python RAG CLI/script as the canonical source instead of manual `_index.md` keyword matching
- [x] **SKILL-02**: User receives a multi-level incident response that first checks deterministic forwarding/routing rules, then only performs RAG/LLM solution synthesis when OOD should handle the ticket
- [x] **LLM-02**: User can opt into privacy-approved Cloud LLM answer synthesis that is grounded in retrieved sources, cites evidence, and preserves local deterministic routing, identifiers, risks, and confidence fields

### Routing, Calendar, and Operational Hand-Off

- [x] **ROUTE-01**: User sees whether a ticket must be forwarded, the target department/team, required SNOW assignment hints, and the duty person from the existing calendar logic whenever a hand-off or escalation is required

### Quality Feedback and Learning Loop

- [x] **FB-02**: User can immediately rate the quality of a proposed solution after receiving it, including whether it solved the ticket, whether routing was correct, and what was missing
- [x] **LEARN-02**: User can asynchronously record the actually successful resolution for a previous ticket/query, reference it from the original suggestion, and receive an alternative solution path in later similar cases
- [x] **KNW-13**: User does not have to manually maintain correct Markdown frontmatter; the system can propose or create normalized knowledge updates from feedback, real resolution notes, concepts, regulations, and source constraints while keeping review/approval explicit before indexing

## Future Requirements

Deferred to later milestones. Tracked to prevent current milestone scope creep.

### Real Data and Integrations

- **DATA-01**: User can import anonymized real ServiceNow/Jira exports after privacy approval
- **DATA-02**: User can run an anonymization and redaction pipeline before real tickets enter the knowledge base
- **DATA-03**: User can compare mock-data and anonymized-real-data evaluation results

### Advanced Evaluation

- **EVAL-08**: User can optionally run LLM-as-judge answer-quality evaluation after explicit privacy approval
- **EVAL-09**: User can compare evaluation reports across historical baselines and trend quality over time
- **EVAL-10**: User can enforce CI regression gates with calibrated thresholds after a stable baseline exists

### Deferred v2 Capabilities

- **RAG-07**: Custom entity extraction (System, Komponente, Fehlertyp)
- **RAG-08**: Multi-turn conversation context
- **KNW-06**: Knowledge API for document ingestion with validation
- **KNW-07**: Freshness scoring (Alter, TTL, superseded-by tracking)
- **KNW-08**: Conflicting sources detection
- **KNW-09**: Document lifecycle management (received -> normalized -> approved -> indexed)
- **KNW-10**: Automatic normalization pipeline for ServiceNow/Jira exports

## Out of Scope

Explicitly excluded from the current milestone.

| Feature | Reason |
|---------|--------|
| Real production ticket import | v1.1 starts with mock data to avoid privacy risk and establish evaluation mechanics first |
| ServiceNow/Jira API integration | API integration is unnecessary until mock import and evaluation quality are validated |
| Mandatory Cloud LLM evaluation | Default evaluation must remain local, deterministic, and privacy-safe |
| LLM-as-judge scoring | Requires explicit privacy approval and separate research |
| Hosted dashboards or tracing platforms | JSON/CLI/Markdown reports are sufficient for the first quality loop |
| Tool execution framework | v1.1 continues to classify command risks only; it must not execute commands |
| Web UI for evaluation | CLI-first workflow is enough for local milestone validation |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| MOCK-01 | Phase 5 | Complete |
| MOCK-02 | Phase 5 | Complete |
| MOCK-03 | Phase 5 | Complete |
| MOCK-04 | Phase 6 | Complete |
| MOCK-05 | Phase 5 | Complete |
| RAG-06 | Phase 11 | Complete |
| ANS-01 | Phase 11 | Complete |
| GRAPH-01 | Phase 11 | Complete |
| CLI-01 | Phase 11 | Complete |
| EVAL-01 | Phase 12 | Complete |
| EVAL-02 | Phase 13 | Complete |
| EVAL-03 | Phase 12 | Complete |
| EVAL-04 | Phase 12 | Complete |
| EVAL-05 | Phase 14 | Complete |
| EVAL-06 | Phase 13 | Complete |
| EVAL-07 | Phase 13 | Complete |
| EVAL-11 | Phase 14 | Complete |
| GRAPH-02 | Phase 15 | Complete |
| KNW-11 | Phase 15 | Complete |
| KNW-12 | Phase 15 | Complete |
| SKILL-01 | Phase 16 | Planned |
| SKILL-02 | Phase 16 | Planned |
| LLM-02 | Phase 16 | Planned |
| ROUTE-01 | Phase 16 | Planned |
| FB-02 | Phase 16 | Planned |
| LEARN-02 | Phase 16 | Planned |
| KNW-13 | Phase 16 | Planned |

**Coverage:**
- v1.1 requirements: 20 total
- v1.2 requirements: 7 total
- Mapped to phases: 27
- Unmapped: 0
- Duplicate mappings: 0

---
*Requirements updated: 2026-05-11 for RAG-backed operational skill, LLM synthesis, and learning loop*
