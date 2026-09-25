package de.muenster.aktivitaeten.activity;

import com.fasterxml.jackson.annotation.JsonValue;
import java.util.Locale;

public enum SourceType {
    SCRAPED,
    USER_SUBMITTED,
    AI_SUGGESTED;

    @JsonValue
    public String value() {
        return name().toLowerCase(Locale.ROOT);
    }
}
