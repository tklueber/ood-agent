# Phase 16: RAG-Backed OOD Skill, LLM Synthesis, and Learning Loop

## Goal

User can operate OOD support through a multi-level skill that uses the Python RAG script as source of truth, handles forwarding and duty calendars before solution work, produces privacy-gated LLM-backed proposals, and learns from immediate plus asynchronous resolution feedback.

## Requirements

- SKILL-01: Installable OOD incident skill derived from the existing `06_OOD-KB/ood-agent` template, with the Python RAG CLI/script as canonical source.
- SKILL-02: Multi-level response flow: deterministic forwarding/routing first, RAG/LLM solution synthesis only when OOD should handle the ticket.
- LLM-02: Privacy-approved Cloud LLM answer synthesis grounded in retrieved sources, with evidence and deterministic fields preserved.
- ROUTE-01: Forwarding response includes target department/team, SNOW hints, calendar link, and duty person from existing calendar logic.
- FB-02: Immediate solution-quality rating after the proposal.
- LEARN-02: Asynchronous actual-resolution capture linked to the original suggestion, usable as future reference and alternative solution path.
- KNW-13: Reviewed knowledge-update proposals from feedback/resolution notes so support people do not manually maintain Markdown frontmatter.

## Source Template

- `/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/ood-agent/SKILL.md`
- `/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/ood-agent/README.md`

## Planned Slices

1. Package and install the RAG-backed OOD incident skill from the existing template.
2. Add deterministic forwarding/calendar hand-off before retrieval and LLM synthesis.
3. Add privacy-gated grounded LLM synthesis for German solution proposals.
4. Add immediate feedback capture and quality signal storage.
5. Add asynchronous actual-resolution capture, alternative path retrieval, and reviewed knowledge-update proposals.

## Guardrails

- Local deterministic routing and RAG remain default.
- Cloud LLM usage must stay behind explicit privacy approval.
- Feedback and resolution notes are learning signals, not automatically trusted indexed knowledge.
- Knowledge updates must be reviewable before indexing to avoid poisoning the KB.
- The support workflow must not require hand-authoring correct YAML frontmatter.
