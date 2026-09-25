package de.muenster.aktivitaeten.activity;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

/** The allowed tags from shared/tags.json (also used by the crawler), grouped by theme. */
@Component
public class TagCatalog {
    private final Map<String, List<String>> groups;
    private final Set<String> allowed;

    public TagCatalog(ObjectMapper objectMapper) throws IOException {
        try (InputStream input = getClass().getClassLoader().getResourceAsStream("tags.json")) {
            if (input == null) {
                throw new IllegalStateException("tags.json not on classpath (shared/tags.json)");
            }
            groups = objectMapper.readValue(input, new TypeReference<LinkedHashMap<String, List<String>>>() {});
        }
        allowed = groups.values().stream().flatMap(List::stream).collect(Collectors.toUnmodifiableSet());
    }

    public Map<String, List<String>> groups() {
        return groups;
    }

    /** Lower-cased, de-duplicated, only allowed tags - in the given order. */
    public List<String> clean(List<String> tags) {
        List<String> cleaned = new ArrayList<>();
        for (String tag : tags) {
            if (tag == null) {
                continue;
            }
            String normalized = tag.trim().toLowerCase(Locale.ROOT);
            if (allowed.contains(normalized) && !cleaned.contains(normalized)) {
                cleaned.add(normalized);
            }
        }
        return cleaned;
    }
}
