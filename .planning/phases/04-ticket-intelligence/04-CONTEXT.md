# Phase 4: Ticket Intelligence - Context

**Gathered:** 2026-05-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 extends `ood query <ticket_text>` from source-attributed retrieval into structured ticket analysis. The user should receive intent recognition, an operational solution path, routing guidance, extracted Policen-/Offertennummern, source-backed uncertainties, and command risk classification.

**In scope:** Structured query analysis contract, deterministic local ticket intelligence, Cloud-LLM grounded explanation drafting when credentials exist, routing logic, identifier extraction, and risk classification for visible commands/actions.

**Out of scope:** Web UI, Teams integration, ServiceNow/Jira API integration, command execution, tool executor workflows, automatic ticket creation, and knowledge lifecycle APIs.

</domain>

<decisions>
## Implementation Decisions

### Structured Answer Contract
- **D-01:** Default human `ood query` output should use operational triage sections: `Einschätzung`, `Lösungsweg`, `Routing`, `Quellen`, `Unsicherheiten`, detected identifiers, and command risks.
- **D-02:** `--json` should preserve the existing Phase 2 query/source fields and add a nested `analysis` object containing at least `intent`, `solution_steps`, `routing`, `identifiers`, `command_risks`, `uncertainties`, and generation/mode metadata.
- **D-03:** `Lösungsweg` should be expressed as concise numbered action steps, grounded by source references when available.
- **D-04:** Low-confidence or no-good-source cases should still return the structured analysis shape, route to `Rückfrage`, list uncertainties, and avoid confident solution steps.

### LLM and Fallback Behavior
- **D-05:** Without Cloud LLM credentials, Phase 4 must still provide deterministic core analysis: local intent heuristics, context-aware ID extraction, deterministic routing defaults, command risk rules, source citations, and uncertainty reporting.
- **D-06:** When Cloud LLM credentials are configured, the LLM may draft `Einschätzung` and `Lösungsweg`, but deterministic code should own intent labels, identifier extraction, routing decision, and command risk labels.
- **D-07:** LLM-generated content must be grounded only in the ticket text and retrieved source excerpts/documents. Missing evidence should be represented as uncertainties instead of unsupported claims.
- **D-08:** Output should expose the generation mode explicitly. JSON should keep `llm_used` and include analysis mode details; human output should briefly note retrieval-only limitations when relevant.

### Routing and Identifiers
- **D-09:** Policen-/Offertennummer extraction should be context-aware: extract identifiers when nearby labels, domain terms, or recognizable prefixes indicate Police or Offerte, rather than harvesting every number.
- **D-10:** Default routing should use deterministic priority rules: actionable high-confidence solution routes to `selbst lösen`; Police ID/domain evidence routes to `weiterleiten Policen`; Offerte ID/domain evidence routes to `weiterleiten Offerten`; missing information or low confidence routes to `Rückfrage`.
- **D-11:** Intent recognition should classify as `Problem`, `Frage`, `Request`, or `Unklar` when evidence is insufficient. Do not force a three-label classification for ambiguous tickets.
- **D-12:** If both Policen- and Offertennummer signals appear, report all extracted identifiers with type and confidence, then route by the context most tied to the current issue. If the context is unclear, route to `Rückfrage`.

### Command Risk Rules
- **D-13:** Risk levels should follow an operational safety ladder: `grün` = read-only diagnostics, `gelb` = reversible low-impact action, `orange` = state/config/data-changing action, and `rot` = destructive, security-sensitive, privileged, or broad-impact action.
- **D-14:** Commands/actions should be detected from both ticket text and retrieved source excerpts/documents, because risky requests can appear in the incoming ticket as well as in runbooks.
- **D-15:** Unknown or ambiguous commands should be conservatively escalated to at least `orange` unless they are clearly read-only.
- **D-16:** Output should show a per-command list/table with risk color, rationale, and origin (`ticket` or source path). JSON should keep structured command-risk entries; human output should show warnings without executing anything.

### the agent's Discretion
- Exact dataclass names and internal module split are flexible as long as the stable CLI/JSON contract above is met.
- Exact heuristic thresholds for confidence, intent, identifier confidence, and command detection are left to research and planning.
- Exact prompt wording for LLM-drafted `Einschätzung`/`Lösungsweg` is flexible as long as the output remains source-grounded and deterministic fields remain code-owned.
- Exact Rich formatting and JSON field ordering are flexible as long as tests can assert the stable schema.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Scope and Requirements
- `.planning/ROADMAP.md` §Phase 4: Ticket Intelligence - Defines the fixed phase goal, dependency on Phase 3, success criteria, and mapped requirements.
- `.planning/REQUIREMENTS.md` §Ticket Intelligence - Defines TIC-01 through TIC-05 for intent recognition, structured answers, routing, command risk, and identifier extraction.
- `.planning/PROJECT.md` §Core Value, §Constraints, and §Context - Defines the ServiceNow-ticket assistant purpose, Markdown-first knowledge base, local MVP, CLI-first approach, Cloud LLM privacy constraint, and no-secrets-in-commits rule.
- `.planning/STATE.md` §Current Position - Captures Phase 04 current focus and success criteria.

### Prior Decisions
- `.planning/phases/01-foundation-cli/01-CONTEXT.md` - Locks uv/Python 3.10+, Typer CLI, flat `index`/`update`/`query`/`reindex` commands, config precedence, `knowledge/`, `data/`, `data/storage`, and CLI output modes.
- `.planning/phases/02-core-rag-engine/02-CONTEXT.md` - Locks recursive Markdown indexing, source-attributed query output, retrieval-only fallback, Cloud LLM usage only when credentials exist, heuristic confidence scoring, and stable `QueryResult` JSON behavior.
- `.planning/phases/03-knowledge-management/03-CONTEXT.md` - Locks warning/reporting-first behavior, manifest-backed metadata diagnostics, duplicate reporting, and keeping CLI rendering thin over OOD-owned dataclass result contracts.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/ood/cli.py` - Existing Typer `query` command loads `Settings`, calls `RagEngine.query(ticket_text)`, and renders `QueryResult`; Phase 4 should extend this path rather than create a new command.
- `src/ood/rag.py` - `RagEngine.query()` already handles index existence, local fallback vs LightRAG, source normalization, LLM availability, and confidence scoring. Ticket intelligence should sit behind this service boundary.
- `src/ood/models.py` - Frozen dataclasses with `to_dict()` methods already define stable CLI JSON contracts; Phase 4 should add/extend OOD-owned models instead of leaking LightRAG internals.
- `tests/test_cli.py` - Existing tests lock JSON/human output patterns for `query`, shared CLI options, and thin rendering behavior.
- `tests/test_rag.py` - Existing tests lock retrieval-only behavior, no-cloud-call behavior without credentials, LLM-backed query mode, source normalization, confidence scoring, and missing-index errors.

### Established Patterns
- CLI is flat and command-oriented; Phase 4 remains an enhancement to `ood query`, not a new UI surface.
- Human output is friendly by default, `--json` is machine-readable, `--verbose` adds diagnostics, and `--quiet` suppresses non-essential output.
- Missing LLM credentials must remain valid for local MVP use and must not send ticket content to a Cloud LLM.
- Cloud LLM calls are permitted only when credentials are configured; prior Phase 2 context allows sending user query plus retrieved source documents when enabled.
- Stable OOD-owned dataclasses isolate CLI/research/planning from LightRAG internal result shapes.

### Integration Points
- Extend `QueryResult` or add nested analysis dataclasses in `src/ood/models.py` for `analysis`, identifiers, routing, intent, uncertainties, solution steps, and command risks.
- Extend `RagEngine._aquery()` to compute deterministic ticket analysis from `query_text` and `sources`, then optionally enrich explanatory fields with LLM output.
- Extend `_emit_query_result()` in `src/ood/cli.py` to render operational triage sections and per-command risk entries while preserving `--json`, `--quiet`, and `--verbose` behavior.
- Add focused tests around local deterministic behavior, LLM/no-LLM boundaries, routing priority, ID extraction, low-confidence `Rückfrage`, and command risk escalation.

</code_context>

<specifics>
## Specific Ideas

- The CLI should feel like an operational triage assistant, not just a search result list.
- Deterministic code should own fields that downstream operations may automate or trust: intent, IDs, routing, risk labels, and mode disclosure.
- LLM output is useful for wording and step drafting, but should not override deterministic safety or routing decisions.
- Ambiguity should produce `Rückfrage` and explicit uncertainties rather than confident speculation.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 04-ticket-intelligence*
*Context gathered: 2026-05-02*
