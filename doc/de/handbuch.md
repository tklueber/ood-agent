# Handbuch: OOD Agent mit Wiki-Extraktion aus `raw/`

Dieses Handbuch beschreibt den kompletten lokalen Workflow, um OOD-Wiki-Exporte aus `/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw` als Wissensbasis in OOD Agent zu indexieren, aktuell zu halten und fuer operative Ticket-Abfragen zu verwenden.

## Zweck

OOD Agent ist ein lokaler RAG-Assistent fuer ServiceNow-Triage. Er durchsucht kuratierte Markdown-Wissensquellen und liefert konkrete Hinweise mit Quellenbezug, Routing-Einschaetzung, Confidence und Sicherheitsmarkierungen fuer gefundene Kommandos.

Der relevante Wiki-Export liegt hier:

```text
/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw
```

Die Dateien sind normale Markdown-Dateien mit YAML-Frontmatter, zum Beispiel Confluence-ID, Confluence-URL und Synchronisationsdatum. OOD akzeptiert auch solche Dateien ohne vollstaendiges OOD-Frontmatter; fehlende OOD-Metadaten werden nur als Warnung gemeldet und blockieren die Indexierung nicht.

## Verzeichnis- und Datenmodell

| Pfad | Bedeutung |
| --- | --- |
| `/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw` | Kanonischer Wiki-Roh-Export fuer diesen Workflow. |
| `data/ood-kb-storage` | Empfohlener lokaler Indexspeicher fuer den `raw`-Export. |
| `data/ood-kb-storage/ood-manifest.json` | Manifest mit Dateihashes, Indexstatus und Diff-Grundlage fuer `update`. |
| `doc/de` und `doc/en` | Repository-Dokumentation in Deutsch und Englisch. |

`data/` ist Runtime-Speicher und gehoert nicht in git.

## Installation

Im Repository ausfuehren:

```bash
uv sync
```

Optionaler Testlauf:

```bash
uv run pytest -q
```

## Konfiguration

Konfigurationsreihenfolge:

1. CLI-Argumente
2. Umgebungsvariablen
3. `.env`
4. Defaults

Wichtige Variablen:

| Variable | Zweck |
| --- | --- |
| `OOD_KNOWLEDGE_DIR` | Markdown-Quellverzeichnis. Fuer diesen Workflow: `/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw`. |
| `OOD_DATA_DIR` | Allgemeines Runtime-Verzeichnis. Default: `data`. |
| `OOD_STORAGE_DIR` | Konkreter Indexspeicher. Empfohlen: `data/ood-kb-storage`. |
| `OOD_LLM_PROVIDER` | Optionaler Cloud-LLM-Anbieter. |
| `OOD_LLM_API_KEY` | Optionaler API-Key. Nur lokal in `.env` oder Environment speichern. |
| `OOD_LLM_MODEL` | Optionales Cloud-LLM-Modell. |

Empfohlene lokale `.env`:

```dotenv
OOD_KNOWLEDGE_DIR=/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw
OOD_STORAGE_DIR=data/ood-kb-storage
```

Keine echten Credentials in Markdown-Dateien oder Commits speichern.

## Indexierungsstrategie

OOD bietet drei Indexbefehle:

| Befehl | Einsatz |
| --- | --- |
| `index` | Erstindexierung ohne explizites Loeschen vorhandener Storage-Artefakte. |
| `reindex` | Sauberer Neuaufbau des Indexes. Empfohlen fuer ersten Lauf und fuer Bereinigung nach geloeschten Quellen. |
| `update` | Inkrementelle Aktualisierung anhand des Manifests. Empfohlen fuer laufende Pflege. |

## Vollstaendige CLI-Referenz

Alle aktuellen OOD-Funktionen sind ueber `uv run ood ...` erreichbar.

| Befehl | Zweck | Typischer Einsatz |
| --- | --- | --- |
| `ood index` | Erstellt einen Index aus Markdown-Dateien. | Wenn ein neuer Quellordner erstmalig aufgenommen werden soll und vorhandene Storage-Artefakte nicht explizit geloescht werden muessen. |
| `ood reindex` | Loescht den Inhalt des gewaehlten Storage-Verzeichnisses und baut den Index sauber neu auf. | Erster produktiver Lauf fuer den Wiki-Export, grosse Export-Aenderungen, Bereinigung geloeschter Quellen. |
| `ood update` | Vergleicht aktuelle Markdown-Dateien mit dem Manifest und indexiert neue/geaenderte Dateien. | Laufende Pflege nach kleinen Wiki-Export-Aenderungen. |
| `ood query "..."` | Fragt den bestehenden Index mit Tickettext oder einer Fachfrage ab. | Operative ServiceNow-Triage, Quellen finden, Routing und Risiken einschaetzen. |
| `ood mock-init` | Erzeugt einen deterministischen synthetischen Mock-Korpus. | Datenschutzsichere Tests und Evaluation ohne echte Wiki-/Ticketdaten. |
| `ood mock-validate` | Validiert Mock-Markierungen, Safety-Funde und Coverage. | Pruefung, ob Mock-Daten klar synthetisch und frei von Golden-Answer-Leakage sind. |

### Gemeinsame Ausgabe- und Diagnoseoptionen

| Option | Befehle | Wirkung |
| --- | --- | --- |
| `--json` | alle Befehle | Gibt maschinenlesbares JSON statt Human-Output aus. |
| `-v`, `--verbose` | `index`, `reindex`, `update`, `query`, `mock-validate` | Zeigt Diagnosekontext; bei Konfigurationsfehlern werden Details sichtbarer. |
| `-q`, `--quiet` | alle Befehle | Unterdrueckt nicht zwingende Human-Ausgaben. |

### Pfadoptionen fuer echte Wissensdaten

Diese Optionen gelten fuer `index`, `reindex`, `update` und `query`.

| Option | Bedeutung |
| --- | --- |
| `--knowledge-dir PATH` | Markdown-Quellverzeichnis. Fuer diesen Workflow: `/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw`. Bei `query` nur relevant, wenn gleichzeitig Einstellungen geladen werden; abgefragt wird der gewaehlte Storage. |
| `--data-dir PATH` | Allgemeines Runtime-Verzeichnis. Wenn `--storage-dir` nicht gesetzt ist, wird daraus `PATH/storage` abgeleitet. |
| `--storage-dir PATH` | Konkretes Index-/Retrieval-Speicherverzeichnis. Muss bei `query` zum vorherigen `index`/`reindex`/`update` passen. |

### Mock-Corpus-Optionen

| Befehl | Option | Bedeutung |
| --- | --- | --- |
| `mock-init` | `--target-dir PATH` | Zielordner fuer generierte Mock-Markdown-Dateien. Default: `knowledge/mock/v1`. |
| `mock-init` | `--dataset NAME` | Dataset-Name im Frontmatter. Default: `mock-v1`. |
| `mock-validate` | `--corpus-dir PATH` | Ordner mit Mock-Markdown-Dateien. Default: `knowledge/mock/v1`. |

### JSON-Vertraege

`index` und `reindex` liefern im JSON-Modus unter anderem `command`, `status`, `indexed_documents`, `skipped_documents`, `storage_dir`, `message`, optional `metadata_warnings`, optional `duplicate_groups` und optional `manifest_path`.

`update` liefert zusaetzlich `diff` mit `new_paths`, `changed_paths`, `unchanged_paths`, `deleted_paths` und `skipped_paths` sowie `schema_version`.

`query` liefert `query`, `answer`, `confidence`, `sources`, `llm_used`, `status` und `analysis`. `analysis` enthaelt `intent`, `assessment`, `solution_steps`, `routing`, `identifiers`, `command_risks`, `uncertainties` und `mode`.

`mock-init` liefert `dataset`, `target_dir`, `document_count`, `generated_paths` und `source_types`.

`mock-validate` liefert `corpus_dir`, `document_count`, `is_safe`, `findings` und `coverage` nach `source_types`, `systems`, `components`, `routing_targets`, `command_risks` und `scenario_categories`.

### Was OOD bewusst nicht macht

- OOD fuehrt keine gefundenen Kommandos aus. Kommandos werden nur klassifiziert.
- `update` entfernt geloeschte Quellen nicht garantiert aus allen Storage-Artefakten; dafuer `reindex` verwenden.
- Ohne Cloud-LLM gibt es keine externe Textgenerierung, sondern lokale Retrieval-/Fallback-Antworten.
- Golden Answers, erwartete Quellen und Evaluationserwartungen gehoeren nicht in indexierte Markdown-Dateien.
- Secrets gehoeren nie in Markdown, README, Dokumentation oder Commits.

## Erstindexierung mit sauberem Neuaufbau

```bash
uv run ood reindex \
  --knowledge-dir "/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw" \
  --storage-dir "data/ood-kb-storage" \
  --json
```

Die Ausgabe enthaelt unter anderem:

- Anzahl indexierter Dokumente
- uebersprungene leere Dokumente
- Metadaten-Warnungen
- Duplicate-Gruppen
- Storage-Pfad
- Manifest-Pfad

## Inkrementelle Aktualisierung

```bash
uv run ood update \
  --knowledge-dir "/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw" \
  --storage-dir "data/ood-kb-storage" \
  --json
```

`update` meldet neue, geaenderte, unveraenderte und geloeschte Pfade. Geloeschte Dateien werden nicht automatisch aus allen Storage-Artefakten entfernt. Wenn geloeschte Quellen bereinigt werden sollen, `reindex` ausfuehren.

## Abfragen

Human-readable Ausgabe:

```bash
uv run ood query \
  "Broker sieht seine Police im SLS Marktplatz nicht" \
  --storage-dir "data/ood-kb-storage"
```

JSON-Ausgabe:

```bash
uv run ood query \
  "Wie loese ich fehlende Rechnungen oder Policen-Dokumente?" \
  --storage-dir "data/ood-kb-storage" \
  --json
```

Query-Ergebnisse enthalten:

| Feld | Bedeutung |
| --- | --- |
| `answer` | Antworttext oder Retrieval-only-Zusammenfassung. |
| `confidence` | Score und Begruendung der Trefferqualitaet. |
| `sources` | Gefundene Markdown-Quellen mit Pfad, Score und Auszug. |
| `analysis.intent` | Deterministisch erkannte Ticket-Intention. |
| `analysis.routing` | Routing-Vorschlag mit Begruendung. |
| `analysis.identifiers` | Erkannte Policen-, Offerten- oder Ticket-IDs. |
| `analysis.command_risks` | Sicherheitsklassifizierung gefundener Kommandos. |
| `llm_used` | Zeigt, ob ein Cloud-LLM verwendet wurde. |

## Datenschutz und Betriebsmodus

Ohne `OOD_LLM_API_KEY` verwendet OOD eine lokale Retrieval-/Fallback-Logik. Dabei werden keine Ticket- oder Wiki-Inhalte an ein Cloud-LLM gesendet.

Mit `OOD_LLM_API_KEY` kann OOD generierte Formulierungen fuer Einschätzung und Loesungsweg nutzen. Das darf nur nach Datenschutzfreigabe verwendet werden. Deterministische Analysebestandteile wie Routing, Identifier und Command-Risk-Klassifizierung bleiben im OOD-Code verankert.

## Quellenqualitaet

Fuer bestmoegliche Diagnostik kann jedes Markdown-Dokument OOD-Frontmatter enthalten:

```yaml
---
quelle: wiki
status: active
system: helix-mf
komponente: servicedesk
type: howto
---
```

Die vorhandenen `raw`-Dateien mit Confluence-Metadaten bleiben trotzdem indexierbar. Fehlende Felder sind Warnungen, keine Fehler.

## Fehlerbehebung

| Problem | Ursache | Loesung |
| --- | --- | --- |
| `IndexMissingError` bei `query` | Es existiert kein Index im angegebenen Storage. | Erst `reindex` mit demselben `--storage-dir` ausfuehren. |
| Keine Treffer oder niedrige Confidence | Query ist zu allgemein oder falscher Storage. | Tickettext konkreter formulieren und `--storage-dir` pruefen. |
| Viele Metadaten-Warnungen | Raw-Export enthaelt nicht alle OOD-Frontmatter-Felder. | Warnungen akzeptieren oder Dateien spaeter mit OOD-Frontmatter anreichern. |
| Geloeschte Quellen erscheinen in Diagnostik | `update` meldet stale/deleted Pfade nur. | `reindex` fuer sauberen Neuaufbau ausfuehren. |
| Cloud-LLM soll nicht genutzt werden | `OOD_LLM_API_KEY` ist gesetzt. | Key aus Environment oder `.env` entfernen. |

## Empfohlener Tagesablauf

```bash
uv run ood update --json
uv run ood query "Tickettext hier einfuegen" --storage-dir "data/ood-kb-storage"
```

Nach groesseren Wiki-Export-Aenderungen:

```bash
uv run ood reindex --json
```

## Verifikation

```bash
uv run pytest tests/test_cli.py tests/test_rag.py tests/test_models.py -q
```

Damit werden CLI- und RAG-Vertraege geprueft, nicht die fachliche Vollstaendigkeit des Wiki-Exports.
