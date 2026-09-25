package de.muenster.aktivitaeten.routing;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

public record WalkingRouteRequest(
        @NotNull @Valid Coordinate origin,
        @NotNull @Positive Double maxWalkingMinutes) {
}
