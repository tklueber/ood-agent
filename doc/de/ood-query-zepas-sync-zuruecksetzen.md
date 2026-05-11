# Technische Erklaerung: `ood query` fuer ZEPAS-Sync zuruecksetzen

Dieses Dokument erklaert die konkrete Ausgabe von:

```bash
uv run ood query \
  "Wie setze ich den ZEPAS Sync zurueck?" \
  --storage-dir "data/ood-kb-storage" \
  --json
```

Die Ausgabe wurde im lokalen Retrieval-only-Modus erzeugt. Es wurde kein Cloud-LLM verwendet.

## Kurzfazit

OOD findet passende Quellen zum Thema ZEPAS-Sync, erzeugt aber keine ausformulierte Antwort. Deshalb ist `answer` `null`, waehrend `sources`, `confidence` und `analysis` trotzdem gefuellt sind.

Das ist wichtig fuer die Interpretation: Diese JSON-Ausgabe ist aktuell keine fertige Support-Antwort. Sie ist ein technischer Retrieval-Befund. OOD sagt damit: "Ich habe relevante Dokumente gefunden und kann sie mit Routing-/Risikosignalen einordnen." OOD sagt noch nicht: "Hier ist die finale Schritt-fuer-Schritt-Anleitung."

Die wichtigsten Signale der konkreten Ausgabe:

| Feld | Wert | Bedeutung |
| --- | --- | --- |
| `answer` | `null` | Keine generierte Antwort, weil kein LLM genutzt wurde. |
| `llm_used` | `false` | Die Anfrage lief lokal ohne Cloud-LLM. |
| `status` | `success` | Es wurden Quellen gefunden. |
| `confidence.score` | `0.97` | Hohe Retrieval-Heuristik durch starke Treffer und viele Quellen. |
| `analysis.intent` | `Frage` | Die Query beginnt mit `Wie` und enthaelt ein Fragezeichen. |
| `analysis.routing.route` | `selbst loesen` | Genuegend Quellen, keine Police-/Offerten-ID, Confidence ueber 0.5. |
| `analysis.mode` | `deterministic` | Ticket-Analyse wurde regelbasiert erzeugt. |

## Warum `answer` `null` ist

`answer` ist nur dann gefuellt, wenn OOD eine generierte Antwort erzeugen kann. In dieser Ausfuehrung ist das nicht der Fall:

- Es sind keine nutzbaren LLM-Credentials aktiv.
- Die lokale Fallback-Suche wird verwendet.
- Die Fallback-Suche liefert nur Quellen und Scores, aber keine synthetisierte Anleitung.
- `analysis.assessment` bleibt ebenfalls `null` und `analysis.solution_steps` bleibt leer.

Das ist gewolltes Datenschutzverhalten: Ohne explizit konfigurierte LLM-Freigabe werden keine Ticket- oder Wiki-Inhalte an einen Cloud-LLM-Anbieter gesendet.

Im Code passiert das in `RagEngine._aquery()`: Wenn die lokale Fallback-Suche aktiv ist, werden `sources` berechnet, `confidence` gescored und `analysis` regelbasiert erzeugt. Danach wird bewusst `QueryResult(answer=None, llm_used=False, ...)` zurueckgegeben.

In der lesbaren CLI-Ausgabe erscheint deshalb sinngemaess:

```text
Einschaetzung:
Retrieval-only mode; Bewertung basiert auf deterministischer Analyse.

Loesungsweg:
Keine belastbaren Loesungsschritte verfuegbar.
```

## Warum diese Quellen gewaehlt wurden

Die lokale Fallback-Suche liest `data/ood-kb-storage/ood-fallback-index.json`. Fuer jedes Dokument wird der Text tokenisiert und mit den Tokens der Query verglichen.

Technisch ist das keine semantische Vektorsuche, sondern eine einfache lokale Wortueberlappung. Diese Fallback-Variante existiert, damit OOD ohne Cloud-LLM und ohne vollstaendige LightRAG-/Embedding-Ausfuehrung lokal nutzbar bleibt.

Die Query enthaelt im Kern diese Tokens:

```text
wie, setze, ich, den, zepas, sync, zurueck
```

Die lokale Scoring-Regel lautet vereinfacht:

```text
score = min(1.0, 0.4 + overlap * 0.2)
```

Wenn es keinen Token-Overlap gibt, wird ein niedriger Rang-Fallback genutzt. Bei drei oder mehr uebereinstimmenden Tokens erreicht ein Dokument bereits `1.0`.

Die ersten Treffer der konkreten Ausgabe sind:

| Rang | Quelle | Score | Warum sie plausibel ist |
| --- | --- | --- | --- |
| 1 | `how-to-hotfix-offerte.md` | `1.0` | Erwaehnt explizit, dass der ZEPAS Sync haengt und ueber einen Admin-Endpunkt geholfen werden kann. |
| 2 | `how-to-zepas-sync-zurucksetzen.md` | `1.0` | Exakter How-to-Titel zum Zuruecksetzen des ZEPAS-Syncs; enthaelt Mustertext und Step-by-Step-Anleitung. |
| 3 | `kundenwert-vererbung-bei-neuen-zepas-personen.md` | `1.0` | Enthält ZEPAS-Bezug, ist aber fachlich nur indirekt relevant. |
| 4 | `wie-impersioniere-ich-einen-user.md` | `1.0` | Teilt allgemeine Tokens wie `wie` und `ich`, ist fuer ZEPAS-Sync wahrscheinlich ein Rauschtreffer. |

Dass `how-to-hotfix-offerte.md` vor `how-to-zepas-sync-zurucksetzen.md` steht, bedeutet nicht zwingend, dass es fachlich besser ist. Beide haben denselben Score `1.0`. Bei Gleichstand bleibt die Reihenfolge aus dem Index beziehungsweise der stabilen Sortierung erhalten.

Ab Score `0.8` erscheinen weitere Dokumente, die einzelne Query-Tokens oder haeufige Woerter teilen. Diese koennen Kontext liefern, sind aber nicht automatisch Loesungsquellen fuer den konkreten ZEPAS-Sync-Fall.

## Wie die Confidence entsteht

Die Confidence ist keine LLM-Selbsteinschaetzung. Sie wird deterministisch aus Retrieval-Signalen berechnet.

Fuer diese Abfrage gelten die relevanten Faktoren:

| Faktor | Konkreter Wert | Beitrag |
| --- | --- | --- |
| Top-Score | `1.0` | Starker bester Treffer. |
| Source Coverage | mindestens 3 Quellen | Maximaler Coverage-Faktor. |
| Score Spread | Top `1.0`, letzter Treffer `0.1` | Maximaler Spread-Faktor. |
| LLM-Faktor | `0.7`, weil kein LLM genutzt wurde | Reduzierter Zusatzfaktor. |

Die Formel im aktuellen Code:

```text
score = top_score * 0.50
      + source_factor * 0.25
      + spread_factor * 0.15
      + llm_factor * 0.10
```

Konkret:

```text
0.50 + 0.25 + 0.15 + 0.07 = 0.97
```

Deshalb lautet die Rationale:

```text
Confidence is limited because no LLM credentials are configured; it is based on retrieval strength, source coverage, and score spread.
```

Wichtig: `0.97` bedeutet hier nicht, dass die Antwort fachlich vollstaendig ist. Es bedeutet, dass die Retrieval-Heuristik starke Treffer sieht. Gerade im lokalen Fallback kann die Confidence durch mehrere lexikalische Treffer hoeher wirken, als die tatsaechliche Antwortqualitaet ist.

## Wie die Ticket-Analyse entsteht

`analysis` wird lokal durch Regeln aus Query, Quellen und Confidence erzeugt.

### Intent

Die Query enthaelt `Wie` und ein Fragezeichen. Deshalb wird `analysis.intent` auf `Frage` gesetzt.

### Routing

Routing folgt dieser Logik:

- Keine Quellen: `Rueckfrage`.
- Confidence unter `0.5`: `Rueckfrage`.
- Police-ID erkannt: `weiterleiten Policen`.
- Offerten-ID erkannt: `weiterleiten Offerten`.
- Sonst bei ausreichenden Quellen: `selbst loesen`.

In dieser Query wurden keine Police- oder Offerten-IDs erkannt. Gleichzeitig gibt es Quellen und eine hohe Confidence. Daher entsteht:

```json
{"route": "selbst loesen", "rationale": "Actionable source with sufficient confidence."}
```

### Identifiers

`analysis.identifiers` ist leer, weil die Query keine erkennbare Police- oder Offertennummer enthaelt. Die aktuelle Erkennung sucht nach Mustern wie `Police 12345`, `Policennummer ...`, `Offerte 12345` oder `Quote ...`.

### Unsicherheiten

`analysis.uncertainties` ist leer, weil:

- Quellen vorhanden sind.
- Confidence nicht unter `0.5` liegt.
- der Intent nicht `Unklar` ist.

Das heisst nicht, dass es keine fachlichen Unsicherheiten gibt. Es heisst nur, dass keine der aktuellen deterministischen Unsicherheitsregeln angeschlagen hat.

## Wie Command-Risks entstehen

OOD fuehrt keine Kommandos aus. Es scannt nur Query und Quellen-Auszüge nach command-aehnlichen Mustern und klassifiziert diese.

Die aktuelle Klassifizierung verwendet vier Risikostufen:

| Risiko | Bedeutung | Beispielmuster |
| --- | --- | --- |
| `gruen` | Read-only Diagnose | `show`, `list`, `status`, `get`, `kubectl get`, `curl -I` |
| `gelb` | reversible operative Aktion | `retry`, `restart` |
| `orange` | zustands-, konfigurations- oder serviceaendernd | `update`, `set`, `write`, `deploy`, `restart service` |
| `rot` | destruktiv oder privilegiert | `rm -rf`, `sudo`, `kubectl delete`, `drop database`, `terraform destroy` |

In der konkreten Ausgabe entstehen mehrere Command-Risks aus den Quellen-Auszügen, zum Beispiel:

| Ursprung | Erkanntes Muster | Risiko | Einordnung |
| --- | --- | --- | --- |
| `how-to-retry-neu-auslosen.md` | `Retry` | `gelb` | Retry wird als reversible Aktion bewertet. |
| `recherche-ob-eine-offerte-geloscht-wurde.md` | `status` | `gruen` | Status-Abfrage ist read-only. |
| `how-to-pvc-vergrossern.md` | `Set` | `orange` | Setzen/Aendern wird konservativ als zustandsaendernd bewertet. |
| `plz-3003-ungultig-update-auf-partner-nicht-moglich.md` | `Update ...` | `orange` | Update wird konservativ als aendernde Aktion bewertet. |

Einige Treffer sind sichtbar grob, weil die Regex im aktuellen Stand auf Textauszuegen arbeitet und nicht nur auf sauber abgegrenzten Shell-Kommandos. Beispiel: Eine Ueberschrift mit `Retry neu ausloesen` kann als command-aehnlicher Treffer erscheinen, obwohl es kein direkt ausfuehrbarer Befehl ist.

## Grenzen der aktuellen Retrieval-only-Ausgabe

Die Ausgabe ist als Retrieval-Diagnose nuetzlich, aber noch keine belastbare Schritt-fuer-Schritt-Antwort.

Aktuelle Grenzen:

- `answer` bleibt `null`; OOD formuliert keine konkrete Anleitung aus den Quellen.
- `solution_steps` bleibt leer, obwohl passende Quellen Loesungsschritte enthalten koennen.
- Die lokale Fallback-Suche ist lexikalisch und versteht keine Synonyme oder Umlaute wie `zurueck` gegen `zurueck`/`zurück` semantisch robust.
- Haeufige Tokens wie `wie`, `ich` oder `den` koennen Rauschtreffer beguenstigen.
- Mehrere Quellen mit Score `1.0` werden nicht fachlich gegeneinander priorisiert.
- Confidence misst Retrieval-Signale, nicht fachliche Vollstaendigkeit oder operative Sicherheit.
- Command-Risks werden aus Auszuegen erkannt und koennen Ueberschriften oder Fliesstext faelschlich als Kommandos behandeln.
- Unsicherheiten sind nur regelbasiert; fachliche Ambiguitaet trotz hoher Confidence wird derzeit nicht zwingend sichtbar.

## Praktische Interpretation fuer den ZEPAS-Fall

Fuer die Frage `Wie setze ich den ZEPAS Sync zurueck?` sollte ein Mensch zuerst die Quelle `how-to-zepas-sync-zurucksetzen.md` pruefen, weil sie den exakten How-to-Fall beschreibt. `how-to-hotfix-offerte.md` ist ebenfalls relevant, weil sie den haengenden ZEPAS-Sync und einen Admin-Endpunkt nennt. Die weiteren Quellen sind eher Kontext- oder Rauschtreffer.

Die aktuelle Ausgabe sagt also:

- OOD hat sehr wahrscheinlich relevante Dokumente gefunden.
- OOD hat bewusst keine Cloud-generierte Antwort erstellt.
- Die naechste operative Aktion ist Quellenpruefung, nicht blindes Ausfuehren erkannter Kommandos.
- Fuer eine echte Endnutzerantwort braucht es entweder eine lokale Antwortsynthese aus Quellen oder einen freigegebenen LLM-Modus.
