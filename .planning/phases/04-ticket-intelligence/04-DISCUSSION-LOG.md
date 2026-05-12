# Phase 4: Ticket Intelligence - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-05-02
**Phase:** 04-ticket-intelligence
**Areas discussed:** Structured answer contract, LLM fallback behavior, Routing and IDs, Command risk rules

---

## Structured Answer Contract

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| Human output structure | Operational triage sections | `Einschätzung`, `Lösungsweg`, `Routing`, `Quellen`, `Unsicherheiten`, detected IDs, and command risks | yes |
| Human output structure | Verbose incident report | Longer narrative with background, diagnosis, options, and evidence | |
| Human output structure | Minimal search summary | Keep current answer/confidence/sources and append a few labels | |
| JSON shape | Nested analysis object | Preserve current query/source fields and add `analysis` with ticket intelligence fields | yes |
| JSON shape | Flatten top-level fields | Add all intelligence fields beside current fields | |
| JSON shape | Replace QueryResult schema | Make JSON entirely ticket-analysis-focused | |
| Lösungsweg format | Numbered action steps | Concise ordered steps, grounded by source references when available | yes |
| Lösungsweg format | Single prose recommendation | Natural prose, less scannable | |
| Lösungsweg format | Evidence-only hints | List relevant excerpts and let user infer actions | |
| Low confidence behavior | Structured Rückfrage result | Return full structure, route to `Rückfrage`, list uncertainties, avoid confident steps | yes |
| Low confidence behavior | No answer result | Return sources/confidence only and say analysis unavailable | |
| Low confidence behavior | Best-effort guess | Always provide likely intent/routing | |

**User's choice:** Operational triage sections, nested analysis object, numbered action steps, structured Rückfrage result.
**Notes:** User chose to move to the next area after these decisions.

---

## LLM Fallback Behavior

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| No-LLM capability | Deterministic core analysis | Local intent heuristics, ID extraction, routing defaults, risk rules, sources, uncertainties | yes |
| No-LLM capability | Retrieval-only plus labels | Current retrieval-only behavior plus minimal labels | |
| No-LLM capability | Require LLM for analysis | Ticket Intelligence only runs with credentials | |
| LLM role | Draft explanation only | Deterministic code owns intent, IDs, routing, risk; LLM drafts Einschätzung/Lösungsweg | yes |
| LLM role | Full analysis proposal | LLM proposes all fields with light validation | |
| LLM role | No LLM in Phase 4 | Fully deterministic phase | |
| Grounding strictness | Only retrieved sources | LLM may only use ticket text plus retrieved source excerpts/documents | yes |
| Grounding strictness | Retrieved plus general knowledge | Allows generic troubleshooting, weaker citations | |
| Grounding strictness | Ticket text only | Avoids source leakage, weakens RAG value | |
| Mode disclosure | Explicit mode fields | JSON includes `llm_used` plus analysis-generation mode; human output notes fallback limitations | yes |
| Mode disclosure | Only existing llm_used | Keep only current boolean | |
| Mode disclosure | Hide implementation mode | Show mode only in verbose output | |

**User's choice:** Deterministic core analysis without credentials; LLM drafts explanation only; strict source grounding; explicit mode fields.
**Notes:** User chose to move to the next area after these decisions.

---

## Routing and IDs

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| Identifier extraction | Context-aware patterns | Extract IDs when nearby labels/domain terms/prefixes indicate Police or Offerte | yes |
| Identifier extraction | Broad number harvesting | Extract many plausible IDs and tag confidence | |
| Identifier extraction | Strict labeled only | Only extract IDs explicitly labeled | |
| Routing default | Deterministic priority rules | Self-solve for actionable high confidence; route by Police/Offerte evidence; Rückfrage for missing info/low confidence | yes |
| Routing default | LLM decides routing | LLM interprets and chooses route | |
| Routing default | Always suggest multiple routes | List all plausible routes with rationale | |
| Intent labels | Three labels plus unclear | Classify as `Problem`, `Frage`, `Request`, or `Unklar` | yes |
| Intent labels | Only three labels | Force Problem/Frage/Request | |
| Intent labels | Fine-grained subtypes | Add detailed subtypes | |
| Mixed IDs | Report all, route by context | Include all IDs with confidence; route by issue context or Rückfrage if unclear | yes |
| Mixed IDs | Prefer Policen | Always route mixed cases to Policen | |
| Mixed IDs | Always Rückfrage | Clarify every mixed identifier case | |

**User's choice:** Context-aware patterns, deterministic priority routing, three labels plus `Unklar`, report all mixed IDs and route by context.
**Notes:** User chose to move to the next area after these decisions.

---

## Command Risk Rules

| Question | Option | Description | Selected |
|----------|--------|-------------|----------|
| Risk definitions | Operational safety ladder | grün=read-only diagnostics, gelb=reversible low-impact, orange=state/config/data-changing, rot=destructive/security/privileged/broad-impact | yes |
| Risk definitions | Simple safe/unsafe mapping | Map green/yellow safe and orange/red unsafe | |
| Risk definitions | Domain-specific only | Define risk only for known insurance/support commands | |
| Detection source | Ticket and retrieved sources | Detect command/action snippets in both ticket text and source excerpts | yes |
| Detection source | Retrieved sources only | Avoid classifying user text as action guidance | |
| Detection source | LLM-generated steps only | Classify commands the generated solution recommends | |
| Ambiguous risk | Conservative escalation | Unknown/ambiguous commands become at least orange unless clearly read-only | yes |
| Ambiguous risk | Unknown category | Use separate unknown marker | |
| Ambiguous risk | Best-effort lower risk | Classify by likely intent | |
| Output format | Per-command table/list | Each command/action has risk color, rationale, and origin | yes |
| Output format | Single overall risk | One risk level for the whole answer | |
| Output format | Only warn orange/red | Show only higher-risk commands in human output | |

**User's choice:** Operational safety ladder, detect from ticket and retrieved sources, conservative escalation, per-command output.
**Notes:** User chose to create context after these decisions.

---

## the agent's Discretion

- Exact dataclass names and module boundaries.
- Exact heuristic thresholds and regex details.
- Exact prompt wording for LLM-drafted sections.
- Exact Rich formatting and JSON field ordering.

## Deferred Ideas

None - discussion stayed within phase scope.
