package de.muenster.aktivitaeten.activity;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.Column;
import jakarta.persistence.Embeddable;
import java.time.LocalDate;
import java.time.LocalTime;

@Embeddable
public class OpeningHours {
    @Column(name = "opening_date")
    private LocalDate date;

    @Column(name = "opening_start", nullable = false)
    private LocalTime start;

    @Column(name = "opening_end", nullable = false)
    private LocalTime end;

    protected OpeningHours() {
    }

    @JsonCreator
    public OpeningHours(@JsonProperty("date") LocalDate date,
                        @JsonProperty("start") LocalTime start,
                        @JsonProperty("end") LocalTime end) {
        this.date = date;
        this.start = start;
        this.end = end;
    }

    @JsonProperty("date")
    public LocalDate getDate() {
        return date;
    }

    public LocalTime getStart() {
        return start;
    }

    public LocalTime getEnd() {
        return end;
    }
}
