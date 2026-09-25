# aktivitaeten_in_muenster

App, die sehenswerte Orte und Aktivitäten in Münster in der Nähe anzeigt — unter Berücksichtigung von verfügbarem Zeitfenster und Erreichbarkeit, mit Fokus auf Entdeckung (offene Vereinstrainings, Meetups, spontane Möglichkeiten).

Monorepo-Struktur:

- [`crawler/`](crawler/README.md) — Web-Crawling + KI-Extraktion, befüllt das Backend über dessen API
- `backend/` — API + Datenbank-Layer
- `frontend/` — Web-App
