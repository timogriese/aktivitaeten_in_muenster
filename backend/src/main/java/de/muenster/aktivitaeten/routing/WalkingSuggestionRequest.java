package de.muenster.aktivitaeten.routing;

import com.fasterxml.jackson.annotation.JsonProperty;
import de.muenster.aktivitaeten.activity.GroupType;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.PositiveOrZero;

import java.util.List;

public record WalkingSuggestionRequest(
        @NotNull @Valid Coordinate origin,
        @NotNull @Positive Double maxWalkingMinutes,
        PreferenceFilter preferences) {

    public record PreferenceFilter(
            String category,
            List<String> tags,
            @JsonProperty("group_type") GroupType groupType,
            @PositiveOrZero @JsonProperty("max_price_eur") Double maxPriceEur,
            @Positive Integer limit) {
    }
}
