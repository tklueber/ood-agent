# Tutorial: OOD Wiki-Exporte indexieren und abfragen

Dieses Tutorial zeigt den schnellsten lokalen Weg, um die Wiki-Exporte aus `/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw` in den OOD-Agent-Index aufzunehmen und fuer Ticket-Abfragen zu nutzen.

## Voraussetzungen

- Repository: `/Users/timo/01_dev/projects/ood-agent`
- Wiki-Export: `/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw`
- Python-Abhaengigkeiten werden mit `uv` installiert.
- Cloud-LLM-Zugang ist optional. Ohne `OOD_LLM_API_KEY` laeuft OOD lokal im Retrieval-only-Modus und sendet keine Ticket- oder Wiki-Inhalte an ein Cloud-LLM.

## 1. Abhaengigkeiten installieren

Wechsle zuerst in das Projektverzeichnis:

```bash
cd /Users/timo/01_dev/projects/ood-agent
```

Pruefe optional, ob der Wiki-Export Markdown-Dateien enthaelt:

```bash
ls "/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw"
```

Installiere dann die Projektabhaengigkeiten:

```bash
uv sync
```

## 2. Index aus dem Wiki-Export neu aufbauen

Nutze fuer den ersten Lauf `reindex`, damit ein sauberer, nur fuer diesen Wiki-Export bestimmter Speicher entsteht.

```bash
uv run ood reindex \
  --knowledge-dir "/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw" \
  --storage-dir "data/ood-kb-storage" \
  --json
```

Erwartung: Die JSON-Ausgabe meldet die Anzahl indexierter Markdown-Dateien, den verwendeten `storage_dir`, moegliche Metadaten-Warnungen und den Pfad zum Manifest. Die Rohdateien muessen nicht verschoben werden.

## 3. Erste Abfrage ausfuehren

```bash
uv run ood query \
  "Offerte bleibt in Rueckfuehrung haengen, was soll ich pruefen?" \
  --storage-dir "data/ood-kb-storage"
```

Die Ausgabe enthaelt:

- `Einschaetzung`
- `Loesungsweg`
- `Routing`
- `Confidence`
- `Quellen`
- `Unsicherheiten`
- erkannte IDs und Command-Risiken

## 4. JSON-Ausgabe fuer Automationen nutzen

```bash
uv run ood query \
  "Wie setze ich den ZEPAS Sync zurueck?" \
  --storage-dir "data/ood-kb-storage" \
  --json
```

## 5. Spaetere Aenderungen inkrementell aufnehmen

Wenn neue oder geaenderte Markdown-Dateien unter `raw/` liegen, reicht meistens `update`:

```bash
uv run ood update \
  --knowledge-dir "/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw" \
  --storage-dir "data/ood-kb-storage" \
  --json
```

`update` vergleicht Dateihashes mit `data/ood-kb-storage/ood-manifest.json` und indexiert nur neue oder geaenderte Dateien. Geloeschte Dateien werden als stale/deleted gemeldet; fuer eine echte Bereinigung danach `reindex` verwenden.

## 6. Optional: Pfade dauerhaft konfigurieren

Lege lokal eine `.env` im Repo an. Diese Datei darf nicht committed werden.

```dotenv
OOD_KNOWLEDGE_DIR=/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/raw
OOD_STORAGE_DIR=data/ood-kb-storage
```

Danach reichen kuerzere Befehle:

```bash
uv run ood reindex --json
uv run ood query "Rabattmenue ist nicht ersichtlich"
uv run ood update --json
```

## 7. Datenschutz-Hinweise

- Keine Secrets in Markdown-Quellen, README, Dokumentation oder Commits speichern.
- Ohne `OOD_LLM_API_KEY` nutzt OOD lokale Fallback-/Retrieval-Logik.
- Mit gesetztem `OOD_LLM_API_KEY` koennen Tickettexte fuer generierte Formulierungen an den konfigurierten Cloud-LLM-Anbieter gehen. Das nur verwenden, wenn die Datenschutzfreigabe vorliegt.
- Runtime-Daten unter `data/` bleiben ausserhalb von git.

## 8. Kurzer Funktionstest

```bash
uv run pytest tests/test_cli.py tests/test_rag.py tests/test_models.py -q
```

Wenn dieser Test und eine Beispielabfrage erfolgreich sind, ist der Wiki-Export lokal im Index nutzbar.
