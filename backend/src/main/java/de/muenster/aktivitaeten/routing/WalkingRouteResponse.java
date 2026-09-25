package de.muenster.aktivitaeten.routing;

import java.util.List;

public record WalkingRouteResponse(List<Result> routes) {
    public record Result(
            Coordinate destination,
            double durationSeconds) {
    }
}
