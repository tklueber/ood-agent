---
name: ood-agent-rag
description: >
  OOD Incident Support mit RAG-CLI. AUTOMATICALLY trigger bei OOD-/heliX-/SNOW-
  Incidents, Police, Offerte, Policennummer, Offertennummer, Bereitschaft,
  OOD-Dienst, #ood-incident, "runbook suchen", "was tun bei", "KB-Artikel finden",
  "ood support", "heliX Fehler", "OOD Fehler". Routing: 15.* → PKV,
  16.* → KMU, 4.005./4.007. → MF.
allowed-tools: Bash
---

# OOD Incident Support (RAG-backed)

Immer Deutsch antworten. Arbeite im Projektverzeichnis `/Users/timo/01_dev/projects/ood-agent`.

## Kanonischer Ablauf

1. Tickettext unverändert übernehmen.
2. Führe ausschließlich die Projekt-CLI aus:

   ```bash
   uv run ood incident "<Incident-Text>" --storage-dir data/ood-kb-storage --json
   ```

3. Parse die JSON-Felder `routing`, `answer`, `confidence`, `sources`,
   `analysis.command_risks`, `analysis.uncertainties`, `feedback` und optional
   `proposal`.
4. Nutze nie `_index.md` als kanonische Suche; die CLI/RAG-Ausgabe ist die einzige
   fachliche Quelle für Matching, Antwort und Quellen.
5. Führe keine in Quellen genannten Commands aus. Commands nur zitieren und mit Risiko
   erklären.
6. Ticketinhalt darf nur an Cloud LLM gesendet werden, wenn die Projektkonfiguration
   `OOD_ALLOW_CLOUD_LLM=true` gesetzt hat und Credentials vorhanden sind. Ohne diese
   Freigabe bleibt die Antwort lokal/extraktiv.

## Routing zuerst

Wenn `routing.should_forward=true`, keine eigene Lösung erfinden. Gib Zielteam,
SNOW-Hinweise, Kalender-Link und `routing.route_reason` aus. Wenn
`routing.continue_to_solution=false`, endet die Bearbeitung nach der Weiterleitung.

## Kalender-Fallbacks

| Bereich | OOD Kalender |
|---------|--------------|
| PKV (NL-PKV) | https://wiki.helvetia.group/x/l5GMK |
| KMU (NL-KMU) | https://wiki.helvetia.group/x/W4mbvg |
| Frontend.MF | https://wiki.helvetia.group/x/TIElfQ |
| OAPS | https://wiki.helvetia.group/x/W61gZw |
| ZEPAS | https://wiki.helvetia.group/x/n9mQFQ |
| ProspectZone / KUPO | https://wiki.helvetia.group/display/FEKUPO/calendars |
| Conversational / Notification | https://wiki.helvetia.group/x/zgE8K |
| SWAD / WAF | https://wiki.helvetia.group/x/f6A5h |

## Antwortformat

- **Weiterleitung** bei Forwarding-Fällen.
- **Lösungsvorschlag** mit `proposal.proposal` oder `answer` bei OOD-Fällen.
- **Quellen** mit Pfad, Score und kurzem Auszug.
- **Risiken** aus `analysis.command_risks`.
- **Unsicherheiten** aus `analysis.uncertainties`.
- **Feedback** mit dem von der CLI gelieferten `feedback.prompt`.
