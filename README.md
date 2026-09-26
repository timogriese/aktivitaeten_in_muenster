# Münster Match (Aktivitaeten_in_muenster)

App, die sehenswerte Orte und Aktivitäten in Münster in der Nähe anzeigt — unter Berücksichtigung von verfügbarem Zeitfenster und Erreichbarkeit, mit Fokus auf Entdeckung (offene Vereinstrainings, Meetups, spontane Möglichkeiten).

Monorepo-Struktur:

- [`backend/`](backend/README.md) — Spring Boot: Aktivitäten-API, SQLite (`activities.db` im Repo-Root), Fußweg-Routing und `POST /api/explore`
- [`crawler/`](crawler/README.md) — Web-Crawling + KI-Extraktion, befüllt das Backend über dessen API
- `frontend/` — Nuxt-Web-App, spricht per Dev-Proxy mit dem Backend

## Farbschema

Die App verwendet warme Cremetöne und gedeckte Grüntöne. Die wichtigsten
UI-Farben sind in [`frontend/app/assets/main.css`](frontend/app/assets/main.css)
definiert:

| Verwendung | Hexcode |
| --- | --- |
| Seitenhintergrund (`--cream`) | `#F7F7EF` |
| Karten und Suchformular | `#FFFEF9` |
| Primärfarbe: Buttons, Logo und aktive Auswahl (`--green`) | `#254F3C` |
| Primäre Buttons bei Hover | `#173C2B` |
| Text auf primären Buttons | `#FFFEF5` |
| Haupttext | `#253C30` |
| Sekundärtext (`--muted`) | `#70776A` |
| Rahmen und Trennlinien (`--line`) | `#E1E4D8` |
| Teilen-Button: Hintergrund | `#EEF2E5` |
| Teilen-Button: Rahmen | `#CCD8BD` |
| Ausgewählte Interessen: Hintergrund | `#EAF0DD` |
| Logo-Punkt | `#7A955A` |
| Kategorie „Natur & draußen“ | `#607B48` |
| Kategorie „Kunst & Kultur“ | `#9B6741` |
| Kategorie „Sport & Bewegung“ | `#3E7E89` |
| Kategorie „Musik & Bühne“ | `#826387` |
| Herz / „Spannend“ | `#35956B` |
| Kreuz / „Nicht für mich“ | `#DC7168` |
| Event-Badge: Hintergrund / Text | `#F7E2C9` / `#784C32` |
| Tastaturfokus | `#96742A` |
| Formularfehler: Hintergrund / Text | `#FBEDE5` / `#954535` |
| Suchfehler: Hintergrund / Text | `#FBECE2` / `#87422C` |

Weitere Abstufungen für Hover, Schatten, Verläufe und Illustrationen stehen
direkt im Stylesheet bzw. in den SVGs. Achtstellige Hexcodes enthalten in den
letzten beiden Stellen zusätzlich den Alphawert für die Deckkraft.

## Lokal starten mit docker compose

docker compose up --build

## Lokal starten mit lokalen dependencies

Voraussetzungen: Java 17+, Maven, uv, Node.js, make. Einmalig die OSM-Datei fürs
Routing laden (siehe [`backend/README.md`](backend/README.md)) und
`crawler/.env` anlegen (siehe [`crawler/README.md`](crawler/README.md)).

```bash
make install
```

```bash
make dev
```

startet Backend (8080), Crawler (8000) und Frontend (http://localhost:3000) in
einem Terminal, Ctrl+C beendet alle. In einem zweiten Terminal:

```bash
make crawl
```

löst einen Crawl-Zyklus aus; die Ergebnisse landen in `activities.db` und sind
direkt im Frontend suchbar. Für einen größeren Import `make crawl-bulk RUNS=20`.
Alle Targets: `make help`.

Die erlaubten Tags stehen in [`shared/tags.json`](shared/tags.json) und werden von
Crawler und Backend gemeinsam genutzt.
