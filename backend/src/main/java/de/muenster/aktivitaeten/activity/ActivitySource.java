package de.muenster.aktivitaeten.activity;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.Column;
import jakarta.persistence.Convert;
import jakarta.persistence.Embeddable;
import java.time.Instant;

@Embeddable
public class ActivitySource {
    @Convert(converter = SourceTypeConverter.class)
    @Column(name = "source_type", nullable = false)
    private SourceType type;

    @Column(name = "source_url")
    private String url;

    @Column(name = "scraped_at")
    private Instant scrapedAt;

    @Column(name = "extraction_confidence")
    private Double extractionConfidence;

    protected ActivitySource() {
    }

    @JsonCreator
    public ActivitySource(@JsonProperty("type") SourceType type,
                          @JsonProperty("url") String url,
                          @JsonProperty("scraped_at") Instant scrapedAt,
                          @JsonProperty("extraction_confidence") Double extractionConfidence) {
        this.type = type;
        this.url = url;
        this.scrapedAt = scrapedAt;
        this.extractionConfidence = extractionConfidence;
    }

    public SourceType getType() {
        return type;
    }

    public String getUrl() {
        return url;
    }

    @JsonProperty("scraped_at")
    public Instant getScrapedAt() {
        return scrapedAt;
    }

    @JsonProperty("extraction_confidence")
    public Double getExtractionConfidence() {
        return extractionConfidence;
    }
}
