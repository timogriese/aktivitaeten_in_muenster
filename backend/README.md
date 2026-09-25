# Backend

This directory is a Spring Boot application that exposes the Java services and
forwards requests to configured Python services.

## Run

The project requires Java 17 and Maven:

```bash
mvn spring-boot:run
```

Activities are persisted in SQLite using Spring Data JPA. By default the
database is created at `./activities.db`; set `DATABASE_PATH` to change the
location. Hibernate creates and updates the `activities` and `activity_tags`
tables automatically. The nested location, opening hours, and source values
are stored as columns on `activities`, while tags are stored in
`activity_tags`.

The checked-in `muenster-regbez-260924.osm.pbf` file is used by default.
GraphHopper imports it on the first request and reuses the graph from
`ROUTING_GRAPH_DIRECTORY`. Override it with `ROUTING_OSM_FILE` when needed.

## Endpoints

`GET /api/health` returns the application status.

Activities are managed through the following CRUD endpoints:

* `GET /activities` lists all activities.
* `POST /activities` creates an activity, or updates an existing activity with
  the same title (returns `201` when created and `200` when updated).
* `GET /activities/{id}` returns one activity.
* `PUT /activities/{id}` partially updates an activity.
* `DELETE /activities/{id}` removes an activity.

`POST /api/routing/walking` accepts the current location and a maximum walking
time in minutes. The service runs one shared Dijkstra search and evaluates all
destinations from `stuff.csv`:

```json
{
  "origin": { "latitude": 51.9623, "longitude": 7.6257 },
  "maxWalkingMinutes": 15
}
```

The response contains only destinations reachable within the time limit. Each
entry includes the destination and its walking duration; unreachable
destinations are omitted.

`POST /api/routing/walking/test` runs the Münster test request using the
destinations in `stuff.csv` and the Münster origin configured in the service.
Override the fixture with `ROUTING_DESTINATIONS_FILE` when needed.

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
