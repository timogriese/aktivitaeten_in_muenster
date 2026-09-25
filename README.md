# Münster Match (Aktivitaeten_in_muenster)

App, die sehenswerte Orte und Aktivitäten in Münster in der Nähe anzeigt — unter Berücksichtigung von verfügbarem Zeitfenster und Erreichbarkeit, mit Fokus auf Entdeckung (offene Vereinstrainings, Meetups, spontane Möglichkeiten).

Monorepo-Struktur:

- [`backend/`](backend/README.md) — Spring Boot: Aktivitäten-API, SQLite (`activities.db` im Repo-Root), Fußweg-Routing und `POST /api/explore`
- [`crawler/`](crawler/README.md) — Web-Crawling + KI-Extraktion, befüllt das Backend über dessen API
- `frontend/` — Nuxt-Web-App, spricht per Dev-Proxy mit dem Backend

## Lokal starten

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
direkt im Frontend suchbar. Alle Targets: `make help`.
