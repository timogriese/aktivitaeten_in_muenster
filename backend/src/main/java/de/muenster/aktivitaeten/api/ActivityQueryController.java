package de.muenster.aktivitaeten.api;

import de.muenster.aktivitaeten.activity.Activity;
import de.muenster.aktivitaeten.activity.ActivityRepository;
import de.muenster.aktivitaeten.activity.GroupType;
import de.muenster.aktivitaeten.activity.TagCatalog;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.stream.Collectors;

import static org.springframework.http.HttpStatus.BAD_REQUEST;

/**
 * Read-only, tag-filtered selection of activities for the frontend. Sits under {@code /api}
 * (unlike the CRUD endpoints at {@code /activities} the crawler writes to), so the Nuxt dev
 * proxy reaches it. The activities are read once and filtered in memory.
 */
@RestController
@RequestMapping("/api/activities")
public class ActivityQueryController {
    private static final String MATCH_ALL = "all";
    private static final String MATCH_ANY = "any";

    private final ActivityRepository activityRepository;
    private final TagCatalog tagCatalog;

    public ActivityQueryController(ActivityRepository activityRepository, TagCatalog tagCatalog) {
        this.activityRepository = activityRepository;
        this.tagCatalog = tagCatalog;
    }

    /**
     * Activities matching the given criteria, e.g.
     * {@code /api/activities?tags=natur,draußen&match=all&limit=5}. Without any parameter this
     * returns the same list as {@code GET /activities}.
     *
     * @param tags  tags from {@code shared/tags.json}, comma-separated or repeated
     * @param match {@code all} (default) requires every tag, {@code any} at least one
     */
    @GetMapping
    public List<Activity> list(
            @RequestParam(required = false) List<String> tags,
            @RequestParam(defaultValue = MATCH_ALL) String match,
            @RequestParam(required = false) String category,
            @RequestParam(name = "group_type", required = false) String groupType,
            @RequestParam(name = "max_price_eur", required = false) Double maxPriceEur,
            @RequestParam(required = false) Integer limit) {
        List<String> wantedTags = wantedTags(tags);
        boolean matchAll = matchAll(match);
        GroupType wantedGroupType = parseGroupType(groupType);
        if (maxPriceEur != null && maxPriceEur < 0) {
            throw new ResponseStatusException(BAD_REQUEST, "max_price_eur must not be negative");
        }
        if (limit != null && limit < 1) {
            throw new ResponseStatusException(BAD_REQUEST, "limit must be at least 1");
        }

        List<Activity> all = new ArrayList<>(activityRepository.findAllWithTags());
        Collections.shuffle(all);
        return all.stream()
                .filter(activity -> matchesTags(activity, wantedTags, matchAll))
                .filter(activity -> category == null || category.equalsIgnoreCase(activity.getCategory()))
                .filter(activity -> wantedGroupType == null || wantedGroupType == activity.getGroupType())
                .filter(activity -> maxPriceEur == null
                        || (activity.getPriceEur() != null && activity.getPriceEur() <= maxPriceEur))
                .limit(limit == null ? Long.MAX_VALUE : limit)
                .toList();
    }

    private static boolean matchesTags(Activity activity, List<String> wantedTags, boolean matchAll) {
        if (wantedTags.isEmpty()) {
            return true;
        }
        Set<String> activityTags = activity.getTags().stream()
                .map(tag -> tag.toLowerCase(Locale.ROOT))
                .collect(Collectors.toSet());
        return matchAll
                ? activityTags.containsAll(wantedTags)
                : wantedTags.stream().anyMatch(activityTags::contains);
    }

    /**
     * The requested tags, normalized by the shared catalog. An unknown tag is rejected instead of
     * being dropped silently, which would return misleadingly broad results.
     */
    private List<String> wantedTags(List<String> tags) {
        if (tags == null) {
            return List.of();
        }
        // Spring already splits "a,b" into two values; drop the empties from "a,,b".
        List<String> requested = tags.stream()
                .filter(tag -> tag != null && !tag.isBlank())
                .toList();
        List<String> cleaned = tagCatalog.clean(requested);
        long distinctRequested = requested.stream()
                .map(tag -> tag.trim().toLowerCase(Locale.ROOT))
                .distinct()
                .count();
        if (cleaned.size() != distinctRequested) {
            throw new ResponseStatusException(BAD_REQUEST,
                    "Unknown tag in " + requested + " - see GET /api/tags");
        }
        return cleaned;
    }

    private static boolean matchAll(String match) {
        String value = match.trim().toLowerCase(Locale.ROOT);
        if (MATCH_ALL.equals(value)) {
            return true;
        }
        if (MATCH_ANY.equals(value)) {
            return false;
        }
        throw new ResponseStatusException(BAD_REQUEST,
                "Unknown match '" + match + "' - use 'all' or 'any'");
    }

    private static GroupType parseGroupType(String groupType) {
        if (groupType == null || groupType.isBlank()) {
            return null;
        }
        try {
            return GroupType.valueOf(groupType.trim().toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException exception) {
            throw new ResponseStatusException(BAD_REQUEST, "Unknown group_type '" + groupType
                    + "' - use 'joinable_group' or 'self_organized'");
        }
    }
}
