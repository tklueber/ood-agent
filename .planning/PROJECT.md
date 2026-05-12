# OOD Agent

## What This Is

Ein RAG-basierter Assistent für ServiceNow-Tickets, der eingehende Fehlerbeschreibungen gegen eine kuratierte Wissensbasis aus Wiki-Exporten, ServiceNow-Fällen, Jira-Bugs und Markdown-Notizen durchsucht und konkrete Lösungswege vorschlägt. Der Agent hilft, wiederkehrende Incidents schneller zu triagieren und zu lösen.

## Core Value

Operative Tickets werden durch intelligente Suche über verteilte Wissensquellen schneller gelöst – mit konkreten Handlungsempfehlungen, Quellenbelegen und Routing-Logik.

## Current Milestone: v1.1 Evaluations- und Real-Data

**Goal:** Das System mit umfangreichen, klar als Mock gekennzeichneten Daten realistisch prüfen, messbar bewerten und gezielt verbessern.

**Target features:**
- Umfangreiche Mock-Wissensbasis mit importierbaren Tickets, Wiki-Artikeln, Jira-Bugs und ServiceNow-Faellen
- Kennzeichnung und sichere Trennung von Mockdaten gegen produktive oder echte Daten
- Evaluationsdatensatz mit erwarteten Treffern, Routing-Ergebnissen und Qualitaetskriterien
- Auswertbare Evaluationslaeufe fuer Retrieval-, Antwort- und Ticket-Intelligence-Qualitaet

## Requirements

### Validated

- [x] Phase 1: Python 3.10+ Projekt mit uv, importierbarem `ood` Package und reproduzierbarem Lockfile validiert
- [x] Phase 1: Konfiguration über `.env`/`OOD_` Umgebungsvariablen und CLI-Overrides validiert
- [x] Phase 1: Runtime- und Indexdaten unter `data/` bleiben außerhalb von Git validiert
- [x] Phase 1: Einfaches CLI mit `index`, `update`, `query` und `reindex` Stubs validiert
- [x] Phase 2: Markdown-Indexing und Clean-Reindex über `RagEngine` und CLI validiert
- [x] Phase 2: Query-Ausgabe mit Quellen, Relevanz-Scores, Excerpts und Confidence validiert
- [x] Phase 2: LightRAG-Integration mit privacy-sicherem Retrieval-only Fallback ohne Cloud-LLM-Credentials validiert
- [x] Phase 3: Inkrementelles `ood update` mit Manifest-Hash-Diff und No-Change-Verhalten validiert
- [x] Phase 3: YAML-Frontmatter, Metadaten-Warnungen, Duplicate-Reports und stale/deleted Path Diagnostics validiert
- [x] Phase 4: Ticket-Intent, strukturierte Analyse, Routing, ID-Extraktion und Command-Risk-Klassifizierung validiert
- [x] Phase 10: Lokales Embedding-Retrieval und privacy-gated Cloud-LLM-Antwortsynthese validiert
- [x] Phase 13: Evaluationslaeufe und Qualitaetsmetriken fuer Retrieval und Ticket Intelligence über `ood eval run`/`cases` mit JSON-Wire-Schema und deutscher Human-Ausgabe validiert
- [x] Phase 14: Observational Baseline, Review-Artefakte, explizite Review-Entscheidungen und review-gated Baseline-Updates validiert

### Active

- [ ] Umfangreiche Mockdaten fuer Tickets, Wiki-Artikel, Jira-Bugs und ServiceNow-Faelle bereitstellen
- [ ] Mockdaten eindeutig kennzeichnen und sicher von echten Daten unterscheidbar machen
- [ ] Import- und Indexing-Flow mit Mockdaten realistisch pruefen
- [ ] Evaluationsdatensatz mit erwarteten Quellen, Antworten, Routing und Risiken definieren

### Out of Scope

- Teams-Webhook-Trigger — später, nach manuellem MVP
- Automatische Wissensrückführung aus gelösten Tickets — später
- Web-Interface — erst nach funktionierendem CLI-Prototyp
- Tool-Executor für Command-Ausführung — erst nur anzeigen und klassifizieren
- ServiceNow/Jira API-Anbindung — MVP startet mit manuellem Markdown-Import

## Context

Das Projekt adressiert ein typisches Support-Problem: Viele operative Tickets ähneln bereits gelösten Fällen oder dokumentierten Wiki-Artikeln, aber die Informationen liegen verteilt vor. Der Agent soll diese Wissensbasis durchsuchbar und nutzbar machen.

**Aktueller Stand:** Phase 14 ist abgeschlossen. Das Projekt hat ein uv-basiertes Python-Fundament, typisierte Konfiguration, LightRAG-Abhängigkeiten, ein `RagEngine`-Service-Layer und ein Typer-CLI, das Markdown indexiert, reindiziert, inkrementell aktualisiert und Query-Ergebnisse mit strukturierter Ticket-Analyse, Routing, Quellen, Unsicherheiten, IDs und Command-Risiken ausgibt. Retrieval läuft standardmäßig lokal über einen Satz-Embedding-Vektorindex; Cloud-LLM-Antwortsynthese bleibt disabled, bis `OOD_ALLOW_CLOUD_LLM=true` und Credentials gesetzt sind. Mit Phase 13 stehen `ood eval run`/`ood eval cases` als black-box Evaluation über `RagEngine.query()` mit deutschem Human-Report und stabilem JSON-Wire-Schema (`schema_version=1`) bereit. Mit Phase 14 kann der erste Baseline-Report bewusst als observational Artifact gespeichert werden; failed/errored Eval-Cases erzeugen Review-Artefakte mit `proposed_fix_type`/`proposed_fix_notes`, und Baseline-Updates sind nur nach explizit genehmigter Review-Entscheidung möglich. v1.1 fokussiert weiterhin auf umfangreiche Mockdaten und reproduzierbare Evaluation, bevor echte oder anonymisierte Produktionsdaten genutzt werden.

**Technische Grundlage:**
- LightRAG als Retrieval-Engine (Graph + Vector Retrieval)
- Markdown als primäres Wissensformat
- Python-basiertes CLI und API
- Persistente Indexdaten außerhalb des Git-Repos

**Zielarchitektur (MVP-Phase):**
- Lokales Python-Projekt mit `knowledge/` Ordner als Markdown-Quelle
- CLI-Befehle: `index`, `reindex`, `update`, `query`
- Strukturiertes Antwortformat mit Lösungsvorschlag, Routing, Quellen, Unsicherheiten

**Spätere Erweiterung:**
- Knowledge API für einheitliche Dokumentannahme (Normalisierung, Metadaten, Dedupe, Freshness)
- Web-UI (Open WebUI oder LibreChat als zentrale Chat-Oberfläche)
- Automatisierung über Teams-Webhook
- Command-Klassifizierung und -Ausführung mit Risikostufen

## Constraints

- **Tech Stack**: Python, LightRAG, Cloud-LLM (nach Datenschutzfreigabe) — Markdown bleibt kanonisches Format
- **Data Privacy**: Ticketinhalte dürfen nur an Cloud-LLM gesendet werden, wenn Datenschutzfreigabe vorliegt
- **Security**: Secrets ausschließlich über `.env`, nie in Markdown-Quellen oder Commits
- **Deployment**: MVP läuft lokal, spätere Deployment-Entscheidung (Proxmox/Hetzner/Vercel)
- **Knowledge Format**: Markdown-Dateien mit YAML-Frontmatter als kanonische Wissenseinheit

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| LightRAG als Retrieval-Engine | Graph + Vector Retrieval kombiniert, gute Balance aus Leistung und Komplexität | Validiert in Phase 2; lokale Retrieval-only Fallbacks bleiben ohne Credentials privacy-sicher |
| Markdown als Wissensformat | Menschenlesbar, versionierbar, tooling-agnostisch | Validiert in Phase 3 mit YAML-Frontmatter und Manifest-Diagnostik |
| CLI vor Web-Interface | Funktionalität validieren, bevor UI-Komplexität hinzukommt | Validiert in Phase 1 und Phase 2 |
| Knowledge API als Quality Gate | Verhindert schlechte Daten im Index durch Normalisierung, Dedupe, Metadaten-Validierung | — Pending |
| Command-Risiko-Klassifizierung | Sicherheitskritisch: verhindert versehentliche Ausführung destruktiver Befehle | Validiert in Phase 4; OOD klassifiziert nur und führt keine Befehle aus |
| Cloud-LLM privacy gate | Ticketinhalte dürfen nur nach expliziter Datenschutzfreigabe an Cloud-LLMs gehen | Validiert in Phase 10; `has_llm_credentials` bleibt Diagnose, `can_use_cloud_llm` steuert Content-send-Pfade |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-11 after Phase 14 completion*
