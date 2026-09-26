package de.muenster.aktivitaeten.activity;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.io.InputStream;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/** Picks a license-free stock photo for an activity, from shared/tag_images.json. */
@Component
public class ActivityImages {
    public record ImageRef(String url, String author, String sourceUrl, String license, String licenseUrl) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    private record Catalog(
            Map<String, List<ImageRef>> tags,
            Map<String, ImageRef> categories,
            @JsonProperty("default") ImageRef fallback) {
    }

    private final Catalog catalog;

    public ActivityImages(ObjectMapper objectMapper) throws IOException {
        try (InputStream input = getClass().getClassLoader().getResourceAsStream("tag_images.json")) {
            if (input == null) {
                throw new IllegalStateException("tag_images.json not on classpath (shared/tag_images.json)");
            }
            catalog = objectMapper.readValue(input, Catalog.class);
        }
    }

    /**
     * The image for the first of the activity's tags that has one (one of its 3 variants, picked
     * deterministically by the activity id so the same activity always shows the same photo),
     * else its category's image, else the default.
     */
    public ImageRef imageFor(Activity activity) {
        for (String tag : activity.getTags()) {
            List<ImageRef> variants = catalog.tags().get(tag.trim().toLowerCase(Locale.ROOT));
            if (variants != null && !variants.isEmpty()) {
                int index = Math.floorMod(activity.getId().hashCode(), variants.size());
                return variants.get(index);
            }
        }
        ImageRef byCategory = catalog.categories().get(activity.getCategory().trim().toLowerCase(Locale.ROOT));
        return byCategory != null ? byCategory : catalog.fallback();
    }
}
