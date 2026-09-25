# Crawler

Findet Aktivitäten in Münster im Web (Suche + Crawling + KI-Extraktion) und befüllt darüber das Backend. Enthält zusätzlich ein Mock-Backend als Platzhalter, solange der echte Backend-Service noch nicht steht.

## Setup

Voraussetzung: [uv](https://docs.astral.sh/uv/).

```bash
make sync
```

entspricht `uv sync` und installiert alle Dependencies in `crawler/.venv`.

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
    scraper_service.py       # Suche/Crawl/KI-Extraktion -> hier arbeitet der Scraper-Teil
    backend_client.py         # ruft die Backend-CRUD-API auf
    crawl_service.py           # orchestriert: scrapen, dann ans Backend pushen
  api/
    routes.py                  # GET /health, POST /crawl

mock_backend/            # Platzhalter-Backend (Port 8001), bis das echte Backend steht
  models.py
  storage_service.py       # In-Memory-Storage
  main.py                    # CRUD: POST/GET/GET-by-id/PUT/DELETE /activities
```

`main.py` -> `api/routes.py` -> `services/crawl_service.py` -> `services/scraper_service.py` + `services/backend_client.py`. Der Scheduler (`scheduler.py`) ruft denselben `crawl_service.run()` auf wie der `/crawl`-Endpoint — ein manueller Trigger und ein Cron-Lauf verhalten sich identisch.

## Datenmodell

Quelle der Wahrheit ist [`app/models/activity.py`](app/models/activity.py). Kurzüberblick:

| Feld | Bedeutung |
|---|---|
| `group_type` | `joinable_group` (bestehende Gruppe, der man sich anschließt) oder `self_organized` (macht man mit der eigenen Gruppe / auf eigene Faust) |
| `opening_hours.date` | konkretes Datum bei `joinable_group` (nächster Termin), `null` bei `self_organized` (an jedem Tag machbar) |
| `opening_hours.start` / `.end` | Uhrzeit — exakter Termin bei fixem Datum, sonst Tagesrahmen (z.B. Öffnungszeiten, Tageslicht-Fenster) |
| `source.type` | `scraped` (klassisch gefunden), `user_submitted`, oder `ai_suggested` (KI hat eine Möglichkeit selbst erkannt, z.B. "schöner Bach") |

## Für den Scraper-Teil: `services/scraper_service.py`

`ScraperService.scrape(query)` ist der Einstiegspunkt und aktuell gemockt: `_mock_llm_results()` liefert zwei feste JSON-Dicts (so, wie sie später vom LLM kommen würden), die über `_parse_llm_result()` gegen `ActivityCreate` validiert werden:

```python
def _parse_llm_result(self, raw: dict) -> ActivityCreate:
    return ActivityCreate.model_validate(raw)
```

Das ist die Stelle, an der später echtes LLM-JSON reinkommt. Beim Ersetzen von `_mock_llm_results` (bzw. der ganzen `scrape`-Logik) durch die echte Suche/Crawl/LLM-Pipeline:

- `scrape()` muss weiterhin `list[ActivityCreate]` zurückgeben — alles danach (Backend-Push, API, Scheduler) bleibt unverändert.
- Bei ungültigem LLM-JSON wirft `_parse_llm_result` eine `pydantic.ValidationError` — das ist gewollt, damit kaputte Extraktionen auffallen statt still falsche Daten zu speichern.

## Mock-Backend ablösen

Sobald das echte Backend steht: `CRAWLER_BACKEND_URL` auf dessen URL setzen (Default: `http://localhost:8001`), `mock_backend/` kann dann raus.
