# Retrieval-Technik des OOD Agent

Dieses Dokument erklaert, wie OOD Agent Markdown-Wissen speichert, indexiert und bei Ticketabfragen wiederfindet. Es beschreibt den aktuellen lokalen Standardpfad und grenzt ihn vom optionalen LightRAG-/Cloud-LLM-Pfad ab.

## Zielbild

OOD Agent ist ein lokaler RAG-Assistent fuer ServiceNow-Triage. Die Wissensbasis bleibt als Markdown kanonisch. Runtime-Artefakte wie Manifest, Vektorindex und Graphindex liegen unter `storage_dir`, typischerweise `data/storage` oder `data/ood-kb-storage`, und gehoeren nicht in git.

Der Retrieval-Prozess soll drei Anforderungen ausbalancieren:

- semantisch aehnliche Loesungsartikel finden
- operative exakte Begriffe wie Ticket-IDs, Fehlercodes, Systemnamen und Komponenten hochranken
- Metadaten und Wikilinks nutzen, ohne Ticket- oder Wiki-Inhalte ungeprueft an ein Cloud-LLM zu senden

## Speicherung der Knowledge Base

Die kanonische Knowledge Base besteht aus Markdown-Dateien unter `knowledge_dir`, standardmaessig `knowledge/`. Fuer den OOD-KB-Export kann der Pfad per `--knowledge-dir` oder `OOD_KNOWLEDGE_DIR` auf einen externen Ordner gesetzt werden.

Jede Datei wird als Wissenseinheit behandelt:

- YAML-Frontmatter liefert strukturierte Metadaten wie `quelle`, `datum`, `status`, `system`, `komponente`, `title` und `type`.
- Der Markdown-Body ist der eigentliche Retrieval-Text.
- Leere Bodies werden uebersprungen.
- Fehlende OOD-Metadaten erzeugen Warnungen, blockieren die Indexierung aber nicht.

Index- und Diagnoseartefakte werden getrennt davon in `storage_dir` geschrieben:

| Artefakt | Zweck |
| --- | --- |
| `ood-manifest.json` | Hashes, Metadaten, Warnungen, Duplicate-Gruppen und Diff-Grundlage fuer `update`. |
| `ood-local-vector-index.json` | Lokaler Vektorindex mit Pfad, Inhalt, Auszug und Embedding je Dokument. |
| `ood-local-graph-index.json` | Lokaler Metadaten-/Graphindex mit Frontmatter-Feldern, Such-Tokens und Wikilink-Kanten. |

`data/` und andere Runtime-Speicher sollen nicht committed werden. Die Markdown-Quellen bleiben die auditierbare Wahrheit.

## Crawling und Indexing

Die Befehle `ood index`, `ood reindex` und `ood update` nutzen denselben Grundablauf:

1. OOD durchsucht `knowledge_dir` rekursiv nach `*.md`.
2. Die Dateien werden deterministisch nach Pfad sortiert.
3. Frontmatter und Body werden getrennt.
4. Pro Dokument werden `content_hash`, `body_hash`, Body-Auszug und Metadatenwarnungen erzeugt.
5. Exakte und nahe Duplikate werden diagnostiziert.
6. Manifest, Vektorindex und Graphindex werden in `storage_dir` geschrieben.

Die Befehle unterscheiden sich im Lebenszyklus:

| Befehl | Verhalten |
| --- | --- |
| `ood index` | Baut Indexartefakte, ohne vorhandenen Storage explizit zu leeren. |
| `ood reindex` | Leert den konfigurierten Storage sicher und baut alles neu auf. |
| `ood update` | Vergleicht aktuelle Hashes mit dem Manifest und indexiert neue oder geaenderte Dateien. |

`update` meldet geloeschte Quellen als stale/deleted. Fuer eine garantierte Bereinigung geloeschter Inhalte ist `reindex` der richtige Befehl.

## Embedding

Der lokale Standardpfad nutzt `sentence-transformers` mit dem Modell `paraphrase-multilingual-MiniLM-L12-v2`. Die Embeddings haben 384 Dimensionen und werden normalisiert erzeugt.

Beim lokalen Indexing wird pro Markdown-Dokument ein Embedding fuer den Body erzeugt. Das Ergebnis wird zusammen mit Pfad, Inhalt und einem maximal 500 Zeichen langen Auszug in `ood-local-vector-index.json` gespeichert. Bei einer Query wird der Querytext mit demselben Modell eingebettet.

Wenn LightRAG verfuegbar und der lokale Fallback nicht aktiv ist, baut OOD eine LightRAG-Instanz mit demselben lokalen Embedding-Modell. Das konfigurierte maximale Embedding-Tokenfenster betraegt 8192 Tokens.

## Chunking

Im aktuellen lokalen Fallback wird ein Markdown-Dokument als eine Retrieval-Einheit gespeichert. Der Begriff `chunks` in Status- und Query-Ausgaben bezeichnet in diesem Pfad faktisch die gespeicherten Dokumenteinheiten im lokalen Vektorindex.

Auszuege werden auf 500 Zeichen begrenzt, damit CLI- und JSON-Ausgaben fokussiert bleiben. OOD gibt standardmaessig nicht den kompletten Quelltext aus. Operatoren oeffnen bei Bedarf die zitierte Markdown-Datei.

Im LightRAG-Pfad kann LightRAG intern eigene Chunks liefern. OOD normalisiert diese Chunks anschliessend in den stabilen `SourceHit`-Vertrag mit Pfad, Score und Auszug.

## Graphaufbau

Parallel zum Vektorindex schreibt OOD den lokalen Graphindex `ood-local-graph-index.json`. Dieser Graph wird deterministisch aus Markdown, Frontmatter und Wikilinks abgeleitet.

Pro Dokument werden unter anderem gespeichert:

- `title`, `type`, `service`, `system`, `component` oder `komponente`
- `keywords`, `keywords_de`, `keywords_en`, `aliases`, `tags` und `related`
- Markdown-Ueberschriften
- Kommandos aus `## Commands`, `## Befehle` oder `## Kommandos`
- ausgehende Wikilinks
- eingehende Linkanzahl
- normalisierte `search_tokens`
- Body-Auszug

Wikilinks werden als Kanten `source -> target` mit Label `wikilink` gespeichert. Ziele werden ueber Dateiname oder Titel-Slug auf vorhandene Dokumente abgebildet. Falls kein Ziel gefunden wird, wird ein Slug-Pfad wie `ziel.md` als Kante notiert.

## Retrieval-Prozess

Bei `ood query "..."` prueft OOD zuerst, ob Indexartefakte im gewaehlten `storage_dir` existieren. Danach gibt es zwei Hauptpfade.

Der lokale Standardpfad wird verwendet, wenn kein Cloud-LLM freigegeben ist und kein LightRAG-Backend genutzt wird:

1. OOD liest `ood-local-vector-index.json`.
2. Der Querytext wird lokal eingebettet.
3. Query-Tokens werden normalisiert extrahiert.
4. Wenn vorhanden, wird `ood-local-graph-index.json` geladen.
5. Jedes Dokument erhaelt semantische, lexikalische, Metadaten- und Graphscores.
6. Die Top 5 Quellen werden als `SourceHit` zurueckgegeben.
7. Ohne Cloud-LLM erzeugt OOD eine konservative extraktive Antwort aus den besten Auszuegen.
8. Ticket-Intelligence bestimmt lokal Intent, Routing, Identifier, Command-Risks und Unsicherheiten.

Der LightRAG-Pfad wird genutzt, wenn LightRAG verfuegbar ist. Ohne Cloud-LLM-Freigabe nutzt OOD `QueryParam(mode="naive")`; mit Datenschutzfreigabe und unterstuetztem Provider nutzt OOD `mode="mix"` und kann zusaetzlich eine generierte Antwort abrufen. Auch dann normalisiert OOD Quellen in den eigenen `QueryResult`-Vertrag.

## Ranking und Scoring

Im lokalen Pfad ist Ranking eine Hybrid-Fusion. Ohne aktiven Graphindex verwendet OOD:

| Komponente | Gewicht |
| --- | ---: |
| Semantik, Cosine Similarity Query zu Dokument | 0.65 |
| Lexikalische Token-Abdeckung | 0.35 |
| Exakter operativer Token-Boost | bis 0.35 |

Mit aktivem Graphindex wird die Gewichtung erweitert:

| Komponente | Gewicht |
| --- | ---: |
| Semantik | 0.20 |
| Lexikalik | 0.15 |
| Metadaten | 0.40 |
| Graphsignale | 0.25 |
| Exakter operativer Token-Boost | bis 0.35 |

Der finale Score wird auf maximal `1.0` begrenzt. Fuer die Ergebnisliste wird der Score auf zwei Dezimalstellen gerundet. Pro Quelle speichert OOD zusaetzlich `score_details` mit den einzelnen Komponenten, Treffern und Gewichten.

Die lexikalische Bewertung misst, wie viele Query-Tokens im Dokument vorkommen. Tokens mit Zahlen, Bindestrichen oder sehr kurzen operativen Begriffen werden als exakte operative Treffer erkannt und koennen einen Boost ausloesen. Das hilft bei Begriffen wie `P-12345`, `ERR-502`, `AKHQ` oder komponentennahen Abkuerzungen.

Die Metadatenbewertung nutzt gewichtete Treffer in Feldern wie Titel, Typ, Service, System, Komponente, Keywords, Aliases, Tags, Ueberschriften, Commands und Search-Tokens. Graphsignale nutzen ausgehende Wikilinks, eingehende Links und Treffer in verlinkten Zieldokumenten.

## Diagnostik

`ood query --verbose` und `ood query --json` zeigen Retrieval-Diagnostik:

- `backend`: `local_vector_index`, `local_vector_graph_index` oder `lightrag`
- `strategy`: verwendete Retrieval-Strategie
- `score_components`: Score-Aufschluesselung je Quelle
- `graph_retrieval`: Status, Artefaktpfad, Dokument- und Kantenanzahl oder Fallback-Grund
- `notes`: kurze Hinweise zum Retrieval-Verhalten

Wenn der Graphindex fehlt oder fehlerhaft ist, faellt OOD automatisch auf hybrides semantisch-lexikalisches Retrieval zurueck und meldet diesen Zustand in `graph_retrieval`.

## Datenschutzgrenze

Lokales Indexing, lokale Embeddings, Graphaufbau, Scoring, Routing und Command-Risk-Klassifikation benoetigen keine Cloud-LLM-Freigabe. Ticket- und Wiki-Inhalte bleiben lokal.

Ein Cloud-LLM darf nur verwendet werden, wenn `OOD_ALLOW_CLOUD_LLM=true` gesetzt ist und gueltige Credentials konfiguriert sind. Konfigurierte Credentials allein reichen nicht. Ohne Freigabe arbeitet OOD retrieval-only und erzeugt Antworten nur aus lokalen Quellen.
