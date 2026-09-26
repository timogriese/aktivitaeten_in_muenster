package de.muenster.aktivitaeten.explore;

import com.fasterxml.jackson.annotation.JsonInclude;
import java.util.List;

/** Mirrors the frontend's ExploreResponse/Activity (frontend/app/types/explore.ts). */
public record ExploreResponse(List<ExploreActivity> activities) {

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record ExploreActivity(
            String id,
            String title,
            String description,
            String kind,
            String category,
            Coordinates location,
            String address,
            String websiteUrl,
            String mapsUrl,
            String startsAt,
            String endsAt,
            String openingHoursText,
            Integer travelTimeMinutes,
            String timingLabel) {
    }

    public record Coordinates(double lat, double lng) {
    }
}
