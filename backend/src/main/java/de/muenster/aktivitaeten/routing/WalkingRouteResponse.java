package de.muenster.aktivitaeten.routing;

import java.util.List;
import java.util.UUID;

public record WalkingRouteResponse(List<Result> routes) {
    public record Result(
            UUID activityId,
            double durationSeconds) {
    }
}
