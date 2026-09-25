package de.muenster.aktivitaeten.explore;

import jakarta.validation.Valid;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import java.time.OffsetDateTime;

/** Mirrors the frontend's ExploreRequest (frontend/app/types/explore.ts). */
public record ExploreRequest(
        @NotNull @Valid Origin origin,
        @NotNull OffsetDateTime startsAt,
        @NotNull @Positive Integer availableMinutes) {

    public record Origin(
            @NotNull @DecimalMin("-90.0") @DecimalMax("90.0") Double lat,
            @NotNull @DecimalMin("-180.0") @DecimalMax("180.0") Double lng) {
    }
}
