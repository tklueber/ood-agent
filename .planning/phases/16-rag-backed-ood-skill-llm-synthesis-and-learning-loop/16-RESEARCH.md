---
phase: 16-rag-backed-ood-skill-llm-synthesis-and-learning-loop
status: complete
date: 2026-05-11
---

# Phase 16 Research: RAG-Backed OOD Skill, LLM Synthesis, and Learning Loop

## Planning-Relevant Findings

- Existing template skill lives at `/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/ood-agent/SKILL.md` and currently uses Read-only `_index.md` keyword matching. Phase 16 should preserve its German response style, trigger phrases, routing tables, OOD calendar links, and setup guidance, but replace manual article scoring with `uv run ood query ... --json` as the canonical search path.
- Current project already exposes stable query contracts through `RagEngine.query()` and `ood query --json`: `QueryResult.answer`, `confidence`, `sources`, `llm_used`, `analysis`, and `retrieval_diagnostics`.
- Privacy boundary is already implemented in `Settings.can_use_cloud_llm`: Cloud LLM content-send paths require both credentials and `OOD_ALLOW_CLOUD_LLM=true`. Phase 16 must reuse this boundary for operational incident synthesis and must not copy Phase 13 eval-runner's deliberate credential-only divergence.
- Deterministic ticket intelligence already exists but routing is too coarse for the skill hand-off requirement. Add a separate operational routing contract for prefix routing, target team, SNOW assignment hints, OOD calendar URL, and duty-person status; run it before any RAG/LLM synthesis.
- Feedback and learning should be artifact-first and review-gated, following Phase 14 patterns. Store immediate ratings, actual resolutions, alternative solution paths, and knowledge update proposals as JSON/Markdown artifacts under ignored `data/`, then require review before indexing.

## Recommended Architecture

1. `src/ood/incident.py` owns operational incident contracts and deterministic routing/calendar hand-off.
2. `src/ood/incident_synthesis.py` owns grounded German synthesis from `QueryResult` plus optional privacy-gated Cloud LLM enrichment.
3. `src/ood/learning.py` owns feedback, actual-resolution, and reviewed knowledge-proposal artifacts.
4. `src/ood/cli.py` exposes workflow commands while keeping existing flat Typer style.
5. `.claude/skills/ood-agent-rag/SKILL.md` is the installable skill artifact that calls the project CLI instead of reading `_index.md`.

## Validation Architecture

- Contract tests prove deterministic routing stops forwarded tickets before RAG is invoked.
- CLI tests use Typer `CliRunner` and tmp `data/` paths, matching existing test patterns.
- Privacy tests assert LLM synthesis does not run when `can_use_cloud_llm` is false and that deterministic routing/identifiers/risks/sources remain present when LLM synthesis is enabled.
- Learning tests assert feedback and actual-resolution artifacts are linked by `suggestion_id`, and knowledge proposals are created as review-required artifacts rather than trusted indexed Markdown.

## Risks and Mitigations

- **Skill overreach:** keep ServiceNow/Jira API integration out of scope; Phase 16 only returns assignment hints and artifacts.
- **Privacy regression:** use `Settings.can_use_cloud_llm`, never `has_llm_credentials`, for operational LLM synthesis.
- **Knowledge poisoning:** resolution feedback creates proposals with `review_status: pending`, not automatically indexed documents.
- **External calendar fragility:** represent duty-person lookup as best-effort status with mandatory calendar URL fallback; do not block routing on browser/calendar access.
