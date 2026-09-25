# Backend

This directory is a Spring Boot application that exposes the Java services and
forwards requests to configured Python services.

## Run

The project requires Java 17+ and Maven. Once, download the OSM extract used for
walking routes (133 MB, not in git) into `backend/data/`:

```bash
curl -L -o data/muenster-regbez-260924.osm.pbf https://download.geofabrik.de/europe/germany/nordrhein-westfalen/muenster-regbez-260924.osm.pbf
```

Then:

```bash
make install   # clean build
make dev       # port 8080
```

`make dev` sets `DATABASE_PATH=../activities.db` (the SQLite file at the repo
root, committed so everyone shares the same data), `ROUTING_OSM_FILE` and
`ROUTING_GRAPH_DIRECTORY` (both under the gitignored `backend/data/`). Running
plain `mvn spring-boot:run` without them uses `./activities.db` and expects the
OSM file on the classpath.

Activities are persisted in SQLite using Spring Data JPA. Hibernate creates and
updates the `activities` and `activity_tags` tables automatically. The nested
location, opening hours, and source values are stored as columns on
`activities`, while tags are stored in `activity_tags`.

GraphHopper imports the OSM extract in the background right after startup (about
half a minute the first time, then loaded from the graph cache in
`ROUTING_GRAPH_DIRECTORY`); routing requests wait until it's ready.

## Endpoints

`GET /api/health` returns the application status.

Activities are managed through the following CRUD endpoints:

* `GET /activities` lists all activities.
* `POST /activities` creates an activity, or updates an existing activity with
  the same title (returns `201` when created and `200` when updated).
* `GET /activities/{id}` returns one activity.
* `PUT /activities/{id}` partially updates an activity.
* `DELETE /activities/{id}` removes an activity.

`POST /api/explore` is what the frontend calls. It takes the frontend's request
shape and returns activities from the database that fit the time budget:

```json
{
  "origin": { "lat": 51.9625, "lng": 7.6285 },
  "startsAt": "2026-09-25T19:00:00+02:00",
  "availableMinutes": 120
}
```

An activity is returned when the walk there takes at most a third of
`availableMinutes` (so there is time on site and for the way back) and its
opening window overlaps the time you would be there. Undated activities repeat
daily (overnight windows like 22:00-05:00 work); dated ones only count on their
date. Results are sorted by walking time (max. 20) and come in the frontend's
`Activity` shape, including `travelTimeMinutes` and a German `timingLabel`.
Crawled English categories are mapped to the frontend's German labels.

`POST /api/routing/walking` accepts the current location and a maximum walking
time in minutes. The service runs one shared Dijkstra search and evaluates all
activities in the database:

```json
{
  "origin": { "latitude": 51.9623, "longitude": 7.6257 },
  "maxWalkingMinutes": 15
}
```

The response contains only activities reachable within the time limit, as
`activityId` and `durationSeconds`, sorted by walking time. `/api/explore` builds
on this.

`POST /api/routing/walking/test` runs the same search from the test origin
configured in the service (near the main station, 30 minutes).

`POST /api/python/{service}` forwards a JSON request to the URL configured for
that service. Configure services with Spring properties or environment
variables, for example:

```yaml
python:
  services:
    recommendations: http://localhost:8000/recommendations
```

The proxy only permits named services configured by the application; request
URLs cannot be supplied by clients.
