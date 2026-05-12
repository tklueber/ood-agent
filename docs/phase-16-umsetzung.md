# Phase 16 Umsetzung: RAG-gestuetzter OOD-Skill und Learning Loop

Phase 16 macht den OOD Agent operativ nutzbar: Ein projektlokaler Skill ruft die Python-CLI als kanonische Quelle auf, prueft Weiterleitungen vor jeder Loesungssuche, erzeugt quellengestuetzte Vorschlaege und speichert Feedback sowie spaetere Ist-Loesungen als lokale, reviewpflichtige Artefakte.

## Umgesetzter Umfang

Phase 16 wurde in fuenf Umsetzungsschnitten abgeschlossen:

| Plan | Schwerpunkt | Ergebnis |
| --- | --- | --- |
| 16-01 | Operational Incident Routing | Deterministische Vorab-Weiterleitung fuer PKV/KMU/MF inklusive SNOW-Hinweisen und Kalender-Fallbacks. |
| 16-02 | OOD RAG Skill | Projektlokaler Skill `.claude/skills/ood-agent-rag/SKILL.md`, der `uv run ood incident ... --json` als einzige fachliche Quelle nutzt. |
| 16-03 | Incident Synthesis | Stabile Vorschlagsartefakte mit `suggestion_id`, Zitaten, Confidence, Privacy-Gate-Status und Retrieval-Diagnostik. |
| 16-04 | Learning-Loop-Artefakte | Lokale JSON-Artefakte fuer Sofortfeedback, Ist-Loesungen und pending Knowledge-Vorschlaege. |
| 16-05 | Operational CLI Workflow | CLI-Kommandos fuer Incident-Bearbeitung, Feedback, Resolution-Capture und Knowledge-Proposals. |

Die relevanten Planungs- und Summary-Artefakte liegen unter `.planning/phases/16-rag-backed-ood-skill-llm-synthesis-and-learning-loop/`.

## Operativer Ablauf

Der vollstaendige Phase-16-Workflow besteht aus sechs Schritten:

1. OOD-KB lokal indexieren oder aktualisieren.
2. Incident ueber `ood incident` bearbeiten.
3. Bei Forwarding-Faellen nach Routing-Ausgabe stoppen.
4. Bei OOD-Faellen den RAG-basierten Vorschlag mit Quellen und Risiken nutzen.
5. Sofortfeedback zum Vorschlag speichern.
6. Spaetere Ist-Loesung erfassen und daraus einen reviewpflichtigen Knowledge-Vorschlag erzeugen.

```bash
uv run ood reindex \
  --knowledge-dir /Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/articles \
  --storage-dir data/ood-kb-storage \
  --json

uv run ood incident "TraceId Kafka AKHQ Ersatzgeschaeft" \
  --storage-dir data/ood-kb-storage \
  --json

uv run ood feedback <suggestion-id> \
  --solved true \
  --useful 5 \
  --correct 4 \
  --routing-correct true \
  --missing-evidence "" \
  --data-dir data

uv run ood resolution <suggestion-id> \
  --resolution-text "Kafka Offset neu gelesen" \
  --resolver "Timo" \
  --source-ticket "INC001" \
  --data-dir data

uv run ood knowledge-proposal <suggestion-id> \
  --data-dir data \
  --json
```

## Route-first Incident Handling

`src/ood/incident.py` implementiert `route_operational_incident()`. Diese Logik laeuft vor Retrieval und vor jeder moeglichen Cloud-LLM-Synthese.

| Erkanntes Praefix | Verhalten | Ziel |
| --- | --- | --- |
| `15.*` | Weiterleiten, keine RAG-Abfrage | PKV |
| `16.*` | Weiterleiten, keine RAG-Abfrage | KMU |
| `4.000.*` oder `4.001.*` | Weiterleiten zur Spartenklaerung, keine RAG-Abfrage | PKV/KMU |
| `4.005.*` oder `4.007.*` | OOD bearbeitet weiter mit MF-Kontext | MF |
| `4.008.*` | OOD bearbeitet weiter mit Unsicherheit | MF/other |
| keine oder unbekannte Nummer | OOD bearbeitet weiter | kein fixes Ziel |

Die Routing-Ausgabe enthaelt `should_forward`, `target_team`, `route_reason`, `detected_number`, `snow_hint`, optional `duty_calendar` und `continue_to_solution`. Weitergeleitete Faelle enden im CLI-Kommando, bevor `RagEngine.query()` aufgerufen wird.

## Projektlokaler OOD RAG Skill

Der Skill liegt in `.claude/skills/ood-agent-rag/SKILL.md` und ist bewusst schlank gehalten:

- Er arbeitet im Projektverzeichnis `/Users/timo/01_dev/projects/ood-agent`.
- Er ruft ausschliesslich `uv run ood incident "<Incident-Text>" --storage-dir data/ood-kb-storage --json` auf.
- Er nutzt nicht mehr `_index.md` als kanonische Suche.
- Er fuehrt keine Commands aus Quellen aus, sondern zitiert sie nur mit Risikoerklaerung.
- Er antwortet auf Deutsch und rendert Weiterleitung, Loesungsvorschlag, Quellen, Risiken, Unsicherheiten und Feedback-Prompt.

Damit ist die CLI/RAG-Ausgabe die einzige fachliche Quelle fuer Matching, Antwort, Quellen und Routing.

## Incident-Vorschlaege und Privacy Gate

`src/ood/incident_synthesis.py` normalisiert ein `QueryResult` in ein `IncidentSolutionProposal`. Das Artefakt enthaelt:

- `suggestion_id`: deterministischer Hash aus Query, Quellenpfaden und Antwort.
- `synthesis_mode`: `no_results`, `local_extractive` oder `llm_grounded`.
- `proposal`: der extraktive oder LLM-gestuetzte Loesungsvorschlag.
- `citations`: Quellenpfad, Score und kurzer Auszug je Treffer.
- `confidence`: uebernommene Confidence aus dem RAG-Ergebnis.
- `llm_used` und `llm_allowed`: tatsaechliche Nutzung und Privacy-Freigabe getrennt ausgewiesen.
- `analysis`: deterministische Ticketanalyse mit Routing, IDs, Command-Risiken und Unsicherheiten.
- `retrieval_diagnostics`: Backend, Strategie, Score-Komponenten und Graphstatus.

Cloud-LLM-Synthese bleibt hinter `Settings.can_use_cloud_llm`. Credentials allein reichen nicht aus; `OOD_ALLOW_CLOUD_LLM=true` ist die explizite Datenschutzfreigabe. Deterministische Felder wie Routing, erkannte IDs, Risiken und Confidence bleiben auch bei LLM-Nutzung erhalten.

## Learning-Loop-Artefakte

`src/ood/learning.py` schreibt lokale JSON-Artefakte unter dem konfigurierten `data_dir`:

| Kommando/Funktion | Pfad | Zweck |
| --- | --- | --- |
| `ood feedback` / `record_feedback()` | `data/feedback/<suggestion-id>.feedback.json` | Sofortbewertung mit `solved`, `useful`, `correct`, `routing_correct`, `missing_evidence`. |
| `ood resolution` / `record_actual_resolution()` | `data/resolutions/<suggestion-id>.resolution.json` | Spaeter tatsaechlich erfolgreiche Loesung mit Resolver und optionaler Ticketreferenz. |
| `ood knowledge-proposal` / `create_knowledge_update_proposal()` | `data/knowledge-proposals/<suggestion-id>.proposal.json` | Reviewpflichtiger Vorschlag fuer einen neuen oder verbesserten Knowledge-Artikel. |

Feedback-Ratings `useful` und `correct` werden auf den Bereich 1 bis 5 validiert. Knowledge-Proposals erhalten immer `review_status: pending` und `source_constraints: ["review_required", "not_auto_indexed"]`.

## Review- und Sicherheitsgrenzen

Phase 16 fuehrt bewusst keine automatische Knowledge-Base-Aenderung aus:

- Keine Feedback- oder Resolution-Notiz wird automatisch nach `knowledge/` kopiert.
- Kein Knowledge-Proposal wird automatisch indexiert.
- Unbekannte Frontmatter-Felder bleiben leer und muessen im Review ergaenzt werden.
- Quellen-Commands werden nie ausgefuehrt.
- Runtime-Artefakte gehoeren unter `data/` und bleiben ausserhalb von Git.

Der manuelle Review-Schritt ist verpflichtend: Erst nach fachlicher Pruefung, Frontmatter-Ergaenzung und manuellem Kopieren in den Knowledge-Corpus darf `ood update` oder `ood reindex` ausgefuehrt werden.

## Neue und geaenderte Implementierung

Phase 16 hat folgende Kernbestandteile eingefuehrt oder erweitert:

| Datei | Rolle |
| --- | --- |
| `src/ood/incident.py` | Route-first Forwarding, SNOW-Hints und Kalender-Fallbacks. |
| `src/ood/incident_synthesis.py` | Normalisierung von RAG-Ergebnissen in operative Vorschlagsartefakte. |
| `src/ood/learning.py` | Lokale Feedback-, Resolution- und Knowledge-Proposal-Artefakte. |
| `src/ood/cli.py` | Neue Kommandos `incident`, `feedback`, `resolution`, `knowledge-proposal`. |
| `.claude/skills/ood-agent-rag/SKILL.md` | Installierbarer projektlokaler OOD-Incident-Skill. |
| `docs/ood-rag-skill.md` | Skill-Installation und Operator-Nutzung. |
| `docs/ood-learning-loop.md` | Vollstaendiger Feedback- und Knowledge-Review-Ablauf. |

## Tests und Verifikation aus Phase 16

Die Phase-16-Summaries dokumentieren folgende erfolgreiche Checks:

| Bereich | Check |
| --- | --- |
| Routing | `uv run pytest tests/test_incident.py -q` |
| Incident-Synthese | `uv run pytest tests/test_incident_synthesis.py -q` |
| RAG-/Modell-Vertraege | `uv run pytest tests/test_rag.py tests/test_models.py -q` |
| Learning Loop | `uv run pytest tests/test_learning.py -q` |
| Operational CLI | `uv run pytest tests/test_cli.py tests/test_learning.py tests/test_incident.py tests/test_incident_synthesis.py -q` |
| CLI Smoke | `uv run ood --help` listet `incident`, `feedback`, `resolution` und `knowledge-proposal`. |

Die aktuellen Tests liegen in `tests/test_incident.py`, `tests/test_incident_synthesis.py`, `tests/test_learning.py` und `tests/test_cli.py`.
