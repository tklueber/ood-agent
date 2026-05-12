# OOD RAG Skill

Diese Seite beschreibt die Nutzung des projektlokalen Phase-16-Skills. Die vollstaendige Umsetzungsdokumentation steht in `docs/phase-16-umsetzung.md`.

## Installation

Den Skill aus `.claude/skills/ood-agent-rag/SKILL.md` in die lokale Skill-Umgebung übernehmen oder direkt projektlokal reviewen. Der Skill arbeitet im Projekt `/Users/timo/01_dev/projects/ood-agent` und ruft die CLI als kanonische Quelle auf.

## Einmaliger Index-Aufbau

```bash
uv run ood reindex --knowledge-dir /Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/articles --storage-dir data/ood-kb-storage --json
```

## Incident-Nutzung

```bash
uv run ood incident "TraceId Kafka AKHQ Ersatzgeschäft" --storage-dir data/ood-kb-storage --json
```

Routing läuft zuerst. PKV/KMU-Weiterleitungen stoppen vor RAG und LLM. OOD-/MF-Fälle laufen weiter in Retrieval und Vorschlagssynthese.

Die JSON-Ausgabe enthaelt `routing`, optional `proposal` und den `feedback.prompt`. Der Skill rendert daraus Weiterleitung, Loesungsvorschlag, Quellen, Risiken, Unsicherheiten und den naechsten Feedback-Schritt.

## Datenschutz

Ticketinhalte werden standardmäßig lokal verarbeitet. Cloud-LLM-Synthese ist nur erlaubt, wenn `OOD_ALLOW_CLOUD_LLM=true` gesetzt ist und Credentials vorhanden sind. Quellen-Commands werden nicht ausgeführt.

## Feedback

Nach einem Vorschlag kann der Nutzer die Qualität erfassen:

```bash
uv run ood feedback <suggestion-id> --solved true --useful 5 --correct 4 --routing-correct true --missing-evidence "" --data-dir data
```

Für den vollständigen Lernpfad siehe `docs/ood-learning-loop.md`.

Der Lernpfad nutzt zusätzlich `ood resolution` für nachträgliche Ist-Lösungen und `ood knowledge-proposal` für reviewpflichtige Knowledge-Updates.

Hinweis: Fuer `ood feedback`, `ood resolution` und `ood knowledge-proposal` ist `--data-dir data` der relevante Speicherort fuer Artefakte. `--storage-dir` betrifft nur Retrieval-Artefakte.
