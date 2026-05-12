# Phase 13: Evaluation Service and CLI Reporting — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-10
**Phase:** 13-evaluation-service-and-cli-reporting
**Areas discussed:** CLI Command Surface, Report Formats (Human + JSON), Cloud-LLM Activation & `llm_used` Visibility, Exit-Code Policy

---

## CLI Command Surface

### Q1: Wie soll die CLI-Struktur für Eval aussehen?

| Option | Description | Selected |
|--------|-------------|----------|
| Subcommands: `ood eval run`, `ood eval cases` | Top-level `eval` mit Subcommands. Erlaubt spätere Erweiterung (`baseline`, `diff`, `review` in Phase 14) ohne Flag-Fluten. | ✓ |
| Einzelner Command: `ood eval` mit Flags | Nur `ood eval --dataset X --case-id Y --json --use-llm`. Weniger Tippen, aber spätere Subkommandos wären ein Bruch. | |
| Flat: `ood evaluate` | Konsistent mit aktuellem flachen Stil, aber Phase-14-Erweiterungen müssten Top-Level-Commands werden. | |

**User's choice:** Subcommands.
**Notes:** Recommended-Pfad — Erweiterbarkeit für Phase 14 war ausschlaggebend.

### Q2: Welches Default-Dataset soll der Eval-Runner nutzen?

| Option | Description | Selected |
|--------|-------------|----------|
| Aus Config/ENV mit Override-Flag | Default-Pfad in Settings (`OOD_EVAL_DATASET`), per `--dataset` überschreibbar. Konsistent mit Knowledge-Dir-Pattern. | ✓ |
| Konvention `evaluation/cases.json`, kein Config-Eintrag | Hardcoded relativer Pfad. Einfacher, aber weniger flexibel für CI. | |
| `--dataset` ist Pflicht-Flag | Kein Default — Pfad jedes Mal angeben. | |

**User's choice:** Aus Config/ENV mit Override-Flag.

---

## Report Formats (Human + JSON)

### Q3: Wie soll die menschenlesbare Ausgabe von `ood eval run` strukturiert sein?

| Option | Description | Selected |
|--------|-------------|----------|
| Header + Summary-Tabelle + Failure-Details | Header (Datum, llm_used, Backend, Korpus-Hash). Aggregierte Metriken-Tabelle. Failures mit Expected-vs-Actual. Pass-Cases nur als Zählung. | ✓ |
| Vollständige Per-Case-Tabelle | Eine Zeile pro Case mit Status ✓/✗. | |
| Minimaler One-Liner | Eine Zusammenfassungszeile. Failures separat per `--verbose`. | |

**User's choice:** Header + Summary + Failure-Details.

### Q4: Welche Sprache für Strings/Labels in den Reports?

| Option | Description | Selected |
|--------|-------------|----------|
| Deutsch | Konsistent mit dem restlichen CLI. `Bestanden: 42`, `Cloud-LLM verwendet: nein`. | ✓ |
| Englisch | Internationaler. Bricht aber Stil-Konsens. | |
| Mischform: deutsche Headers, englische Metric-Keys | Headers deutsch, Keys wie `hit@1`, `mrr` englisch. | |

**User's choice:** Deutsch.
**Notes:** Metric-Keys im JSON bleiben trotzdem englisch (Fachbegriffe).

### Q5: Wie tief soll das JSON-Schema pro Case sein?

| Option | Description | Selected |
|--------|-------------|----------|
| Volle Diagnostik pro Case | Pro Case: query, expected_sources, actual_sources mit Scores, match-Bool, alle Metriken, retrieval_diagnostics, analysis, llm_used. Plus `meta` und `summary`. Skill- und CI-tauglich. | ✓ |
| Schlank: nur Metriken | Pro Case nur Metriken + match-Status, keine Quellenlisten. | |
| Zwei JSON-Modi: `--json` schlank, `--json-full` voll | User wählt explizit. Mehr CLI-Komplexität. | |

**User's choice:** Volle Diagnostik pro Case.

---

## Cloud-LLM Activation & `llm_used` Visibility

### Q6: Welche Bedingungen müssen erfüllt sein, damit Eval Cloud-LLM nutzt?

| Option | Description | Selected |
|--------|-------------|----------|
| ENV + explizites `--use-llm` Flag | Beides nötig: `OOD_ALLOW_CLOUD_LLM=true` UND `--use-llm` pro Lauf. | |
| Nur ENV reicht | `OOD_ALLOW_CLOUD_LLM=true` reicht, konsistent mit `ood query`. | |
| Nur `--use-llm` Flag, kein ENV-Check | Eval umgeht globalen Privacy-Gate. | |
| **(User-Eingabe — siehe Klärung Q6.1)** | | ✓ |

**User's choice:** Free-text response: "Ich möchte das Cloud LLM standardmäßig ist - sollten die credentials vorhanden sein. Kein extra flag oder use-llm; Fallback ohne".

### Q6.1 (Klärung): Was genau aktiviert den Cloud-LLM-Pfad in der Eval?

| Option | Description | Selected |
|--------|-------------|----------|
| Existierender Gate aus `ood query` (ENV + Credentials) | Eval respektiert `can_use_cloud_llm`. Beides muss da sein. | |
| Nur Credentials-Check (kein ENV nötig) | Sobald API-Key vorhanden, wird LLM genutzt — auch ohne `OOD_ALLOW_CLOUD_LLM`. | ✓ |
| Anders | Free-text. | |

**User's choice:** Nur Credentials-Check (kein ENV nötig).
**Notes:** Bewusste Abweichung von der `ood query`-Semantik. Privacy-Verantwortung liegt bei der Credential-Verwaltung, nicht bei einem zusätzlichen Runtime-Schalter.

### Q7: Wo erscheint `llm_used: true|false` in der menschenlesbaren Ausgabe?

| Option | Description | Selected |
|--------|-------------|----------|
| Erste Header-Zeile, hervorgehoben bei true | Zweite Zeile nach Datum/Backend. Bei `true` mit Marker (`»LLM«`). | ✓ |
| Nur im Footer/meta-Block | Steht am Ende. | |
| Beides: Header UND pro-Case | Überbestimmt. | |

**User's choice:** Erste Header-Zeile, hervorgehoben bei true.

### Q8: Wie geht der Runner mit Cases um, die `expected_llm_answer`-Felder haben, wenn LLM inaktiv ist?

| Option | Description | Selected |
|--------|-------------|----------|
| Skippen mit Markierung `skipped:llm_required` | Case zählt nicht als Pass/Fail; im Report mit `status: skipped`. | ✓ |
| Trotzdem auswerten gegen extraktive Antwort | Riskiert systematische Fails. | |
| Fail mit klarem Grund | Lauf wird rot ohne echten Grund. | |

**User's choice:** Skippen mit Markierung.

---

## Exit-Code Policy

### Q9: Wann soll `ood eval run` mit Exit-Code ≠0 beenden?

| Option | Description | Selected |
|--------|-------------|----------|
| Nur bei Hard-Errors | Dataset nicht ladbar, JSON kaputt, Code-Crash, Knowledge-Index fehlt. Cases die scheitern → Exit 0. | ✓ |
| Hard-Errors + jede Case-Failure | Wenn auch nur ein Case fehlschlägt → Exit ≠0. | |
| Konfigurierbar per Flag `--strict` | Default Exit 0, aber `--strict` macht Failures zu Exits. | |

**User's choice:** Nur bei Hard-Errors.
**Notes:** EVAL-05 verbietet harte Schwellen ohne Baseline. Konsistent mit dem Phase-14-Plan, dass Gates später kommen.

### Q10: Was passiert bei einem einzelnen Case-Crash (RagEngine wirft Exception)?

| Option | Description | Selected |
|--------|-------------|----------|
| Case als `errored` markieren, weitere Cases laufen weiter | Kein vorzeitiger Abbruch. Stacktrace-Snippet im Report. Lauf-Exit bleibt 0. | ✓ |
| Lauf abbrechen, Exit ≠0 | Erste Exception stoppt alles. | |
| Lauf weiter, ABER finaler Exit ≠0 | Cases laufen weiter, aber Lauf wird rot. | |

**User's choice:** Case als `errored` markieren, weitere Cases laufen weiter.

---

## Claude's Discretion

User explicitly deferred to planner:
- Output destination (stdout default + optional `--out <path>`; auto-snapshots = Phase 14)
- Case filters beyond `--case-id`
- Engine reuse vs per-case isolation
- Exact `meta` field set (within the suggested superset)
- Progress reporting style during long runs
- Error/warning channel (stderr vs JSON field)

## Deferred Ideas

- Auto-snapshot to `evaluation/reports/<timestamp>.json` → Phase 14 (Baseline)
- Historical comparison / diff between runs → Phase 14 / EVAL-09
- `--strict` Exit mode → Phase 14 / EVAL-10
- Tag/source filters → when dataset grows
- LLM-as-judge → EVAL-08 (deferred)
- LightRAG architecture review → tracked separately, baseline from this phase is the prerequisite to answer it
