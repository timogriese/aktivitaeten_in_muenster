# Crawler

Findet Aktivitäten in Münster im Web (Suche + Crawling + KI-Extraktion) und befüllt darüber das Backend. Enthält zusätzlich ein Mock-Backend als Platzhalter, solange der echte Backend-Service noch nicht steht.

## Setup

Voraussetzung: [uv](https://docs.astral.sh/uv/).

```bash
make sync
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

Zwei Terminals:

```bash
make backend   # Mock-Backend auf Port 8001
```

```bash
make crawler   # Crawler-Service auf Port 8000
```

Crawl manuell auslösen:

```bash
make crawl     # POST /crawl
```

Der Crawler läuft zusätzlich automatisch alle 30 Minuten im Hintergrund (siehe `app/scheduler.py`, Intervall konfigurierbar über `CRAWLER_CRAWL_INTERVAL_MINUTES`).

Alle Make-Targets: `make help`.

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

mock_backend/            # Platzhalter-Backend (Port 8001), bis das echte Backend steht
  models.py
  storage_service.py       # In-Memory-Storage
  main.py                    # CRUD: POST/GET/GET-by-id/PUT/DELETE /activities
```

`main.py` -> `api/routes.py` -> `services/crawl_service.py` -> `services/query_service.py` + `services/scraper_service.py` + `services/backend_client.py`. Der Scheduler (`scheduler.py`) ruft denselben `crawl_service.run()` auf wie der `/crawl`-Endpoint — ein manueller Trigger und ein Cron-Lauf verhalten sich identisch. `/crawl` nimmt bewusst keinen Input entgegen: `CrawlService` holt sich die Suchanfrage selbst von `QueryService`, statt sie vom Aufrufer zu bekommen.

## Datenmodell

Quelle der Wahrheit ist [`app/models/activity.py`](app/models/activity.py). Kurzüberblick:

| Feld | Bedeutung |
|---|---|
| `group_type` | `joinable_group` (bestehende Gruppe, der man sich anschließt) oder `self_organized` (macht man mit der eigenen Gruppe / auf eigene Faust) |
| `opening_hours.date` | konkretes Datum bei `joinable_group` (nächster Termin), `null` bei `self_organized` (an jedem Tag machbar) |
| `opening_hours.start` / `.end` | Uhrzeit — exakter Termin bei fixem Datum, sonst Tagesrahmen (z.B. Öffnungszeiten, Tageslicht-Fenster) |
| `source.type` | `scraped` (klassisch gefunden), `user_submitted`, oder `ai_suggested` (KI hat eine Möglichkeit selbst erkannt, z.B. "schöner Bach") |

## Scraper-Teil: `services/scraper_service.py` + `services/tavily_client.py` + `services/llm_client.py`

`ScraperService.scrape(query)` ist der Einstiegspunkt. Pipeline:

1. **Search** — Tavily `POST /search` für `query` (Default: `CRAWLER_DEFAULT_QUERY`) mit `include_raw_content: markdown` liefert Kandidaten-URLs **inklusive** ihres Seiteninhalts in einem einzigen Call (kein separater Scrape-Schritt/-Kosten nötig).
2. **Extraktion** — das Markdown geht an unser eigenes LLM (`llm_client.py`, MSHack Gateway, kostenloses Modell) mit einem Prompt, der genau ein Objekt gemäß Schema zurückgibt (`response_format: json_object`). Das Schema wird per `ActivityCreate.model_json_schema()` aus dem Pydantic-Modell generiert, sodass Extraktion und Validierung nie auseinanderlaufen.
3. **Validierung** — das JSON wird per `_parse_llm_result()` gegen `ActivityCreate` validiert. Müll-Ergebnisse (leeres `{}`, Platzhalter-Titel wie "Not Found") werden vorher schon verworfen.

Damit läuft pro Crawl-Zyklus nur noch **ein** Tavily-Call (statt Search + einzelne Scrapes), bei 1000 kostenlosen Credits/Monat. Die eigentliche LLM-Extraktion läuft über das kostenlose Gateway-Modell, parallel (Semaphore = `CRAWLER_EXTRACTION_CONCURRENCY`). Es wird **keine JSON-Datei** geschrieben: Die Objekte existieren nur im Speicher und werden erst nach erfolgreicher Validierung ans Backend gepusht. Eine kaputte Extraktion wird geloggt und übersprungen — nur „nicht kaputte" Aktivitäten landen in der Datenbank, eine einzelne schlechte Seite lässt den Rest des Crawls stehen.

## Query-Planung: `services/query_service.py` + `services/llm_client.py`

`QueryService.next_query()` fragt das LLM (MSHack AI Gateway, `CRAWLER_LLM_MODEL`, Default
`DeepSeek-V4-Flash`, OpenAI-kompatibel) nach einer neuen Suchanfrage für Aktivitäten in Münster.
Schlägt der Call fehl (fehlender Key, Netzwerkfehler, ...), fällt es auf einen festen
Beispiel-Pool zurück, damit ein Crawl-Zyklus trotzdem laufen kann.

## Mock-Backend ablösen

Sobald das echte Backend steht: `CRAWLER_BACKEND_URL` auf dessen URL setzen (Default: `http://localhost:8001`), `mock_backend/` kann dann raus.
