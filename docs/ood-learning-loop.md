# OOD Learning Loop

Phase 16 verbindet Incident-Bearbeitung, Feedback und Wissensverbesserung über lokale, reviewpflichtige Artefakte.

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

## 4. Tatsächliche Lösung nachtragen

```bash
uv run ood resolution <suggestion-id> --resolution-text "Kafka Offset neu gelesen" --resolver "Timo" --source-ticket "INC001" --data-dir data
```

## 5. Knowledge-Vorschlag erstellen

```bash
uv run ood knowledge-proposal <suggestion-id> --data-dir data --json
```

Der Vorschlag erhält `review_status: pending` und wird nicht automatisch indexiert.

## 6. Manuelles Review und KB-Update

Prüfe den Vorschlag fachlich, ergänze Frontmatter und Body, und kopiere nur geprüfte Inhalte manuell in den Knowledge-Corpus. Erst danach den Index aktualisieren:

```bash
uv run ood update --knowledge-dir /Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/articles --storage-dir data/ood-kb-storage --json
```

Phase 16 schreibt genehmigtes Wissen nicht automatisch nach `knowledge/` und führt keine Commands aus Quellen aus.
