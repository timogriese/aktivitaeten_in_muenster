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

und die echten Werte in `crawler/.env` eintragen (Firecrawl-Key, LLM-Zugangsdaten). `.env` ist
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
    query_service.py          # denkt sich die naechste Suchanfrage aus
    scraper_service.py         # Suche/Crawl/Extraktion -> orchestriert die Firecrawl-Pipeline
    firecrawl_client.py         # schlanke Firecrawl-REST-Client (Search + JSON-Extraktion)
    backend_client.py           # ruft die Backend-CRUD-API auf
    crawl_service.py             # orchestriert: Query holen, scrapen, ans Backend pushen
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

## Scraper-Teil: `services/scraper_service.py` + `services/firecrawl_client.py`

`ScraperService.scrape(query)` ist der Einstiegspunkt und ruft Firecrawl direkt über die REST-API auf (Client: `firecrawl_client.py`). Pipeline:

1. **Search** — `POST /v1/search` für `query` (Default: `CRAWLER_DEFAULT_QUERY`) liefert Kandidaten-URLs.
2. **Extraktion** — je URL `POST /v2/scrape` mit einem `json`-Format-Objekt: Firecrawl extrahiert serverseitig (LLM-basiert) genau ein Objekt gemäß Schema. Das Schema wird per `ActivityCreate.model_json_schema()` aus dem Pydantic-Modell generiert, sodass Extraktion und Validierung nie auseinanderlaufen.
3. **Validierung** — das JSON wird per `_parse_llm_result()` gegen `ActivityCreate` validiert.

Die Extraktion läuft parallel (Semaphore = `CRAWLER_FIRECRAWL_CONCURRENCY`, dem Account-Limit). Es wird **keine JSON-Datei** geschrieben: Die Objekte existieren nur im Speicher und werden erst nach erfolgreicher Validierung ans Backend gepusht. Eine kaputte Extraktion wirft eine `pydantic.ValidationError`, wird geloggt und übersprungen — nur „nicht kaputte" Aktivitäten landen in der Datenbank, eine einzelne schlechte Seite lässt den Rest des Crawls stehen.

## Mock-Backend ablösen

Sobald das echte Backend steht: `CRAWLER_BACKEND_URL` auf dessen URL setzen (Default: `http://localhost:8001`), `mock_backend/` kann dann raus.
