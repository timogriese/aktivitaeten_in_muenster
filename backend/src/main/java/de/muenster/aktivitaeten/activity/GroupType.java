package de.muenster.aktivitaeten.activity;

import com.fasterxml.jackson.annotation.JsonValue;
import java.util.Locale;

public enum GroupType {
    JOINABLE_GROUP,
    SELF_ORGANIZED;

    @JsonValue
    public String value() {
        return name().toLowerCase(Locale.ROOT);
    }
}
