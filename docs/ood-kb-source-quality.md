# OOD-KB Source Quality Guide

Use this guide when improving the external OOD-KB Markdown corpus for local graph/metadata retrieval.

## Recommended frontmatter

```yaml
title: How to find TraceId in Kafka message
type: runbook
service: Kafka
system: AKHQ
component: Ersatzgeschäft
problem_type: trace_lookup
keywords:
  - TraceId
  - Kafka message
aliases:
  - trace id
  - traceid
  - correlation id
related:
  - how-to-splunk
  - uno-fehler-offerte-verarbeitung
supersedes: []
last_verified: 2026-05-08
owner: OOD Team
quelle: Confluence
```

## TraceId/Kafka synonym tips

For TraceId articles, include variants operators actually type:

- `trace id`, `traceid`, `TraceId`
- `correlation id`
- `Kafka message`
- `AKHQ`
- `Ersatzgeschäft`

Put canonical terms in `keywords` and alternate spellings in `aliases` so metadata scoring can explain the match.

## Wikilink patterns

Create bidirectional context between:

- troubleshooting articles and related tickets
- runbooks and system/component notes
- error-code notes and concrete incidents
- TraceId lookup guides and Splunk/AKHQ query examples

Example body link: `Siehe [[how-to-splunk]] und [[uno-fehler-offerte-verarbeitung]].`

## Commands and risk markers

Use a `## Commands` section for operational snippets and add a nearby risk marker:

```markdown
## Commands

Risk: grün — read-only log lookup.

```bash
kubectl logs deploy/akhq | grep TraceId
```
```

OOD classifies command risks but never executes commands.

## Freshness and source attribution

- Add `last_verified` or `last_synced` so stale articles can be flagged.
- Add `owner` so someone can fix low-quality or outdated sources.
- Add at least one source field: `quelle`, `confluence_url`, `snow_incidents`, or `jira`.

## Title quality

Use specific, operator-searchable titles. Prefer `How to find TraceId in Kafka message` over `Kafka Info`.
