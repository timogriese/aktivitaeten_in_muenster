# Crawler

Findet Aktivitäten in Münster im Web (Suche + Crawling + KI-Extraktion) und befüllt darüber das Backend. Enthält zusätzlich ein Mock-Backend als Platzhalter, solange der echte Backend-Service noch nicht steht.

## Setup

Voraussetzung: [uv](https://docs.astral.sh/uv/).

```bash
make install
```

entspricht `uv sync` und installiert alle Dependencies in `crawler/.venv`.

### Secrets

```bash
cp .env.example .env
```

und die echten Werte in `crawler/.env` eintragen (Tavily-Key, LLM-Zugangsdaten). `.env` ist
per `.gitignore` ausgeschlossen und wird nie committet — `.env.example` (ohne echte Werte) ist
die einzige Datei davon, die im Repo landet. Alle Settings lassen sich zusätzlich per
Umgebungsvariable überschreiben (`CRAWLER_`-Prefix, siehe `app/core/config.py`).

## Starten

Normalerweise vom Repo-Root mit `make dev` (startet Backend, Crawler und Frontend
zusammen). Nur der Crawler:

```bash
make dev            # Crawler-Service auf Port 8000, pusht an das Spring-Backend (8080)
```

Ohne Java geht es auch gegen den Python-Mock (`make mock-backend`, Port 8001) mit
`CRAWLER_BACKEND_URL=http://localhost:8001`.

Crawl manuell auslösen:

```bash
make crawl     # POST /crawl
```

Der Crawler läuft zusätzlich automatisch alle 30 Minuten im Hintergrund (siehe `app/scheduler.py`, Intervall konfigurierbar über `CRAWLER_CRAWL_INTERVAL_MINUTES`).

Alle Make-Targets: `make help`. Gleiches Schema (`install`/`dev`/`lint`) auch im [`frontend/`](../frontend/Makefile)
— vom Repo-Root aus lassen sich alle Bereiche zusammen starten/installen/linten, siehe
[`../Makefile`](../Makefile).

## Architektur

```
app/                     # Crawler-Service (Port 8000)
  main.py                # FastAPI-App, startet den Scheduler beim Hochfahren
  scheduler.py            # Cron-Job (alle 30 Min.), ruft denselben Code wie /crawl
  core/
    config.py              # Settings, u.a. CRAWLER_BACKEND_URL
  models/
    activity.py             # Pydantic-Modelle: die "Aktivität" nach unserem Schema
  services/
    query_service.py          # denkt sich per LLM die naechste Suchanfrage aus
    llm_client.py               # schlanker Client fuer die MSHack AI Gateway (OpenAI-kompatibel)
    scraper_service.py           # Suche+Content (Tavily) + Extraktion (eigenes LLM)
    tavily_client.py               # schlanker Tavily-Client (Search inkl. Seiteninhalt)
    backend_client.py             # ruft die Backend-CRUD-API auf
    crawl_service.py               # orchestriert: Query holen, scrapen, ans Backend pushen
  api/
    routes.py                  # GET /health, POST /crawl

mock_backend/            # Python-Stand-in fuers Backend (Port 8001), fuer offline/ohne Java
  models.py
  storage_service.py       # In-Memory-Storage
  main.py                    # CRUD: POST/GET/GET-by-id/PUT/DELETE /activities
```

`main.py` -> `api/routes.py` -> `services/crawl_service.py` -> `services/query_service.py` + `services/scraper_service.py` + `services/backend_client.py`. Der Scheduler (`scheduler.py`) ruft denselben `crawl_service.run()` auf wie der `/crawl`-Endpoint — ein manueller Trigger und ein Cron-Lauf verhalten sich identisch. `/crawl` nimmt bewusst keinen Input entgegen: `CrawlService` holt sich die Suchanfragen selbst von `QueryService`, statt sie vom Aufrufer zu bekommen. Response-Shape: `{"queries": [...], "found": N, "created": N, "updated": N}` (`created`/`updated` siehe Dedup unten).

## Datenmodell

Quelle der Wahrheit ist [`app/models/activity.py`](app/models/activity.py). Kurzüberblick:

| Feld | Bedeutung |
|---|---|
| `group_type` | `joinable_group` (bestehende Gruppe, der man sich anschließt) oder `self_organized` (macht man mit der eigenen Gruppe / auf eigene Faust) |
| `opening_hours.date` | konkretes Datum bei `joinable_group` (nächster Termin), `null` bei `self_organized` (an jedem Tag machbar) |
| `opening_hours.start` / `.end` | Uhrzeit — exakter Termin bei fixem Datum, sonst Tagesrahmen (z.B. Öffnungszeiten, Tageslicht-Fenster) |
| `source.type` | `scraped` (klassisch gefunden), `user_submitted`, oder `ai_suggested` (KI hat eine Möglichkeit selbst erkannt, z.B. "schöner Bach") |

## Scraper-Teil: `services/scraper_service.py` + `services/tavily_client.py` + `services/llm_client.py`

`ScraperService.scrape_many(queries)` läuft für alle Queries (aktuell 5, siehe Query-Planung
unten) parallel und fasst die Ergebnisse zusammen; ruft dafür pro Query `scrape(query)` auf.
Pipeline pro Query:

1. **Search** — Tavily `POST /search` für `query` (Default: `CRAWLER_DEFAULT_QUERY`) mit `include_raw_content: markdown` liefert Kandidaten-URLs **inklusive** ihres Seiteninhalts in einem einzigen Call (kein separater Scrape-Schritt/-Kosten nötig).
2. **Extraktion** — das Markdown geht an unser eigenes LLM (`llm_client.py`, MSHack Gateway, kostenloses Modell) mit einem Prompt, der genau ein Objekt gemäß Schema zurückgibt (`response_format: json_object`). Das Schema wird per `ActivityCreate.model_json_schema()` aus dem Pydantic-Modell generiert, sodass Extraktion und Validierung nie auseinanderlaufen.
3. **Validierung** — das JSON wird per `_parse_llm_result()` gegen `ActivityCreate` validiert. Müll-Ergebnisse (leeres `{}`, Platzhalter-Titel wie "Not Found") werden vorher schon verworfen.

Pro Query läuft nur **ein** Tavily-Call (statt Search + einzelne Scrapes), bei 1000 kostenlosen
Credits/Monat — bei 5 parallelen Queries pro Crawl-Zyklus also 5 Tavily-Calls/Zyklus (mehr dazu
unten bei der Query-Planung). Die eigentliche LLM-Extraktion läuft über das kostenlose
Gateway-Modell, parallel über alle Queries hinweg (Semaphore = `CRAWLER_EXTRACTION_CONCURRENCY`,
begrenzt die Gesamt-Parallelität, nicht pro Query). Es wird **keine JSON-Datei** geschrieben:
Die Objekte existieren nur im Speicher und werden erst nach erfolgreicher Validierung ans
Backend gepusht. Eine kaputte Extraktion wird geloggt und übersprungen — nur „nicht kaputte"
Aktivitäten landen in der Datenbank, eine einzelne schlechte Seite lässt den Rest des Crawls
stehen.

## Query-Planung: `services/query_service.py` + `services/llm_client.py`

`QueryService.next_queries()` generiert pro Crawl-Zyklus **5 Suchanfragen parallel**, jede mit
ihrem eigenen Prompt/Thema (siehe `_MODE_HINTS` in `query_service.py`): organisierte
Sport-/Bewegungsgruppen, organisierte Kultur-/Kreativgruppen, coole Natur-/Outdoor-Spots, coole
soziale/spontane Aktivitätsideen, einmalige Community-Events. Das deckt pro Zyklus eine breite
Mischung ab statt nur einer Kategorie. Schlägt ein einzelner LLM-Call fehl (fehlender Key,
Netzwerkfehler, ...), fällt nur diese eine Query auf einen festen Beispielwert zurück — die
anderen vier laufen normal weiter.

## Duplikate: Upsert per Titel

`mock_backend` legt bei `POST /activities` nichts doppelt an: `ActivityStore.create_or_update()`
sucht nach einer vorhandenen Aktivität mit demselben Titel (normalisiert, ohne
Groß-/Kleinschreibung) und aktualisiert die bestehende statt eine neue anzulegen. So bleiben
wiederholt gefundene Aktivitäten (z.B. dieselbe Trainingsgruppe aus zwei verschiedenen Queries,
oder ein erneuter Crawl-Zyklus) aktuell statt sich zu vervielfachen. Antwortet mit `201` bei
echtem Neuanlegen, `200` bei Update — `CrawlService` zählt das für `created`/`updated` im
`/crawl`-Ergebnis aus. Da `BackendClient.push_activities` die Aktivitäten nacheinander (nicht
parallel) an das Backend schickt, greift der Dedup-Check auch innerhalb eines einzelnen
Crawl-Zyklus, falls zwei der 5 Queries dieselbe Aktivität finden.

## Backend

Default ist das Spring-Backend (`CRAWLER_BACKEND_URL`, Default `http://localhost:8080`),
das denselben Upsert-per-Titel-Vertrag wie `mock_backend` umsetzt. Lehnt das Backend
einzelne Aktivitäten ab (z.B. leere Beschreibung), werden sie geloggt und übersprungen
(`rejected` im `/crawl`-Ergebnis) — der Rest des Crawls läuft weiter. Ist das Backend gar
nicht erreichbar, schlägt der Crawl fehl.
