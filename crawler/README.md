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

## Scraper-Teil: `services/scraper_service.py`

`ScraperService.scrape_many(queries)` läuft für alle Queries eines Zyklus parallel. Pipeline pro
Query:

1. **Search**: Tavily (`tavily_client.py`) liefert Kandidaten-URLs inklusive Seiteninhalt als
   Markdown in einem Call. Die Suche ist auf Deutschland beschränkt, Social-Media- und
   Video-Seiten (Facebook, Instagram, TikTok, YouTube, …) sind ausgeschlossen.
2. **Extraktion**: Unser LLM (`llm_client.py`, MSHack Gateway, kostenlos) füllt pro Seite ein
   `ExtractedActivity` (`models/extraction.py`, bewusst getrennt vom Backend-Format). Der Prompt
   verlangt deutschen Text, Tags nur aus [`shared/tags.json`](../shared/tags.json) und Zeiten nur,
   wenn sie auf der Seite stehen. Übersichts- und Top-10-Seiten, Selbsthilfe- und Beratungsangebote,
   Shops sowie alles außerhalb Münsters bekommt `{}`.
3. **Prüfen & Vervollständigen** (`_to_activity`), sonst wird verworfen, mit Grund im Log:
   - Text auf Englisch → raus.
   - Keine Zeiten auf der Seite → raus. Ausnahme: öffentliche Orte draußen (Tag `draußen`,
     `self_organized`) bekommen ein Tageslicht-Fenster 08–20 Uhr plus Tag `tagsüber`.
   - Wöchentliche Termine (`weekdays`) → `date` = nächster passender Wochentag.
   - Einmalige Events in der Vergangenheit → raus.
   - Tags: nur erlaubte, mindestens einer. `kostenlos` nur, wenn die Seite „kostenlos“ sagt
     (ein unbekannter Preis wird als 0 gespeichert, weil das Backend einen verlangt, aber
     nicht als `kostenlos` getaggt).
   - Adresse muss „Münster“ oder PLZ 481xx enthalten und wird per Photon (OpenStreetMap)
     geocodiert, innerhalb Münsters. Das LLM liefert keine Koordinaten mehr, die hat es
     früher geraten. Treffer, die nur „die Stadt“ sind, gelten als zu vage.

Ein Zyklus kostet 5 Tavily-Credits (Free-Tier: 1000/Monat). Im Probelauf kamen etwa 3 von 25
Seiten durch: Qualität vor Menge.

## Tags: [`shared/tags.json`](../shared/tags.json)

Feste Tag-Liste, gruppiert nur zur Übersicht. Crawler und Backend lesen dieselbe Datei: Der
Crawler gibt sie dem LLM vor und filtert dessen Auswahl, das Backend verwirft unbekannte Tags
beim Speichern und liefert die Liste unter `GET /api/tags` aus. Neue Tags nur dort eintragen.

## Query-Planung: `services/query_service.py`

Pro Zyklus 5 Suchanfragen parallel, je Modus eine: organisierte Sportgruppe, organisierte
Kultur-/Kreativgruppe, Natur-Spot, soziale Aktivität, einmaliges Event. Jeder Modus bekommt
ein zufälliges Unterthema (z.B. Bouldern, Töpfern, Rieselfelder, Pubquiz) und die zuletzt
gestellten Anfragen, damit ein großer Import nicht dieselben Seiten wiederfindet. Die
Anfragen sind auf Deutsch und zielen auf Seiten zu *einem* Angebot. Schlägt ein LLM-Call fehl,
fällt nur diese Query auf einen festen Beispielwert zurück.

## Großer Import

```bash
make crawl-bulk RUNS=20
```

(vom Repo-Root, während `make dev` läuft): 20 Zyklen nacheinander, also 100 Tavily-Credits.
Achtung: Der automatische Crawl alle 30 Minuten kostet ebenfalls je 5 Credits;
`CRAWLER_CRAWL_INTERVAL_MINUTES=0` in `crawler/.env` schaltet ihn ab.

## Duplikate

Das Backend führt per Titel zusammen (gleicher Titel = Update statt neuer Eintrag). Zusätzlich
gleicht der Crawler vor dem Push mit den vorhandenen Aktivitäten ab (`services/dedup.py`):
Liegt eine neue Aktivität unter 150 m von einer bestehenden und ist ihr Titel fast gleich
(„Aasee“ und „Aasee Münster“, „Kreativhaus“ und „Kreativ-Haus“), übernimmt sie deren Titel.
Die Regel ist bewusst streng: „Malkurs“ und „Töpferkurs“ im selben Haus bleiben getrennt,
denn ein falsches Zusammenführen überschreibt Daten. Gepusht wird nacheinander, damit das
auch innerhalb eines Zyklus greift.

## Backend

Default ist das Spring-Backend (`CRAWLER_BACKEND_URL`, Default `http://localhost:8080`),
das denselben Upsert-per-Titel-Vertrag wie `mock_backend` umsetzt. Lehnt das Backend
einzelne Aktivitäten ab (z.B. leere Beschreibung), werden sie geloggt und übersprungen
(`rejected` im `/crawl`-Ergebnis) — der Rest des Crawls läuft weiter. Ist das Backend gar
nicht erreichbar, schlägt der Crawl fehl.
