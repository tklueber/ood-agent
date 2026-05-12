# OOD Learning Loop

Phase 16 verbindet Incident-Bearbeitung, Feedback und Wissensverbesserung ueber lokale, reviewpflichtige Artefakte. Die vollstaendige Umsetzungsdokumentation steht in `docs/phase-16-umsetzung.md`.

## Zielbild

Der Learning Loop macht aus operativer Nutzung keine automatisch vertrauenswuerdige Knowledge-Base-Aenderung. Feedback, Ist-Loesungen und Knowledge-Vorschlaege werden lokal unter `data/` gespeichert, bleiben aus Git heraus und muessen vor jeder Uebernahme in den Knowledge-Corpus fachlich geprueft werden.

## 1. OOD-KB neu indexieren

```bash
uv run ood reindex --knowledge-dir /Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/articles --storage-dir data/ood-kb-storage --json
```

## 2. Incident bearbeiten

```bash
uv run ood incident "TraceId Kafka AKHQ Ersatzgeschäft" --storage-dir data/ood-kb-storage --json
```

Routing läuft vor RAG. Forwarding-Fälle werden nicht synthetisiert.

## 3. Sofortfeedback erfassen

```bash
uv run ood feedback <suggestion-id> --solved true --useful 5 --correct 4 --routing-correct true --missing-evidence "" --data-dir data
```

Das Feedback wird als `data/feedback/<suggestion-id>.feedback.json` gespeichert. `useful` und `correct` muessen Werte von 1 bis 5 sein.

## 4. Tatsächliche Lösung nachtragen

```bash
uv run ood resolution <suggestion-id> --resolution-text "Kafka Offset neu gelesen" --resolver "Timo" --source-ticket "INC001" --data-dir data
```

Die Ist-Loesung wird als `data/resolutions/<suggestion-id>.resolution.json` gespeichert und bleibt ueber die `suggestion_id` mit dem urspruenglichen Vorschlag verknuepft.

## 5. Knowledge-Vorschlag erstellen

```bash
uv run ood knowledge-proposal <suggestion-id> --data-dir data --json
```

Der Vorschlag erhält `review_status: pending` und wird nicht automatisch indexiert.

Der Vorschlag liegt unter `data/knowledge-proposals/<suggestion-id>.proposal.json` und enthaelt leere oder generische Frontmatter-Felder, die im Review bewusst ergaenzt werden muessen.

## 6. Manuelles Review und KB-Update

Prüfe den Vorschlag fachlich, ergänze Frontmatter und Body, und kopiere nur geprüfte Inhalte manuell in den Knowledge-Corpus. Erst danach den Index aktualisieren:

```bash
uv run ood update --knowledge-dir /Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/articles --storage-dir data/ood-kb-storage --json
```

Phase 16 schreibt genehmigtes Wissen nicht automatisch nach `knowledge/` und führt keine Commands aus Quellen aus.

## Sicherheitsgrenzen

- `ood incident` beendet weiterzuleitende PKV/KMU-Faelle vor jeder RAG-Abfrage.
- Cloud-LLM-Synthese ist nur mit `OOD_ALLOW_CLOUD_LLM=true` und Credentials erlaubt.
- Feedback und Ist-Loesungen sind Lernsignale, keine automatisch indexierten Quellen.
- Knowledge-Proposals bleiben `pending`, bis ein Mensch sie fachlich freigibt.
- Commands aus Quellen werden nie ausgefuehrt.
