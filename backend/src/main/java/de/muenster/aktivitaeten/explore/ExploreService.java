package de.muenster.aktivitaeten.explore;

import de.muenster.aktivitaeten.activity.Activity;
import de.muenster.aktivitaeten.activity.ActivityImages;
import de.muenster.aktivitaeten.activity.OpeningHours;
import de.muenster.aktivitaeten.activity.ActivityRepository;
import de.muenster.aktivitaeten.activity.TagCatalog;
import de.muenster.aktivitaeten.activity.Location;
import de.muenster.aktivitaeten.explore.ExploreResponse.Coordinates;
import de.muenster.aktivitaeten.explore.ExploreResponse.ExploreActivity;
import de.muenster.aktivitaeten.explore.ExploreResponse.ImageCredit;
import de.muenster.aktivitaeten.routing.Coordinate;
import de.muenster.aktivitaeten.routing.WalkingRouteRequest;
import de.muenster.aktivitaeten.routing.WalkingRouteResponse;
import de.muenster.aktivitaeten.routing.WalkingRouterService;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.Set;

/**
 * Finds activities that fit a time budget: reachable on foot from the origin, and open (or
 * happening) while the user would be there.
 */
@Service
public class ExploreService {
    private static final ZoneId ZONE = ZoneId.of("Europe/Berlin");
    // The walk there may take at most this share of the available time, leaving time on site
    // and for the way back.
    private static final double MAX_TRAVEL_SHARE = 1.0 / 3.0;
    private static final int MAX_RESULTS = 40;
    private static final DateTimeFormatter CLOCK = DateTimeFormatter.ofPattern("HH:mm");

    // The crawler's fixed categories (crawler/app/models/extraction.py) mapped to the German
    // labels the frontend shows and picks icons by.
    private static final Map<String, String> CATEGORY_LABELS = Map.ofEntries(
            Map.entry("sport", "Sport & Bewegung"),
            Map.entry("nature", "Natur & draußen"),
            Map.entry("culture", "Kunst & Kultur"),
            Map.entry("creative", "Kunst & Kultur"),
            Map.entry("music", "Musik & Bühne"),
            Map.entry("food", "Essen & Trinken"),
            Map.entry("market", "Märkte & Stadtleben"),
            Map.entry("social", "Treffen & Geselliges"));

    private final ActivityRepository activityRepository;
    private final WalkingRouterService walkingRouterService;
    private final TagCatalog tagCatalog;
    private final ActivityImages activityImages;

    public ExploreService(ActivityRepository activityRepository, WalkingRouterService walkingRouterService,
                          TagCatalog tagCatalog, ActivityImages activityImages) {
        this.activityRepository = activityRepository;
        this.walkingRouterService = walkingRouterService;
        this.tagCatalog = tagCatalog;
        this.activityImages = activityImages;
    }

    // Read-only so activity.getTags() (lazy-loaded, needed for the image lookup below) can still
    // be read on the plain findAll() path - open-in-view is off, so without a transaction the
    // Hibernate session is already gone by the time toResponse() runs.
    @Transactional(readOnly = true)
    public ExploreResponse explore(ExploreRequest request) {
        Set<String> preferredTags = Set.copyOf(tagCatalog.clean(
                request.preferredTags() == null ? List.of() : request.preferredTags()));
        List<Activity> activities = preferredTags.isEmpty()
                ? activityRepository.findAll() : activityRepository.findAllWithTags();
        if (activities.isEmpty()) {
            return new ExploreResponse(List.of());
        }

        double maxTravelMinutes = request.availableMinutes() * MAX_TRAVEL_SHARE;
        WalkingRouteRequest walking = new WalkingRouteRequest(
                new Coordinate(request.origin().lat(), request.origin().lng()), maxTravelMinutes);
        // Only activities reachable within maxTravelMinutes come back.
        Map<String, Double> secondsByActivity = new HashMap<>();
        for (WalkingRouteResponse.Result route : walkingRouterService.route(walking).routes()) {
            secondsByActivity.put(route.activityId(), route.durationSeconds());
        }

        ZonedDateTime start = request.startsAt().atZoneSameInstant(ZONE);
        ZonedDateTime end = start.plusMinutes(request.availableMinutes());

        List<Match> matches = new ArrayList<>();
        for (Activity activity : activities) {
            Double seconds = secondsByActivity.get(activity.getId());
            if (seconds == null) {
                continue;
            }
            Duration travel = Duration.ofSeconds(Math.round(seconds));
            ZonedDateTime arrival = start.plus(travel);
            ZonedDateTime leave = end.minus(travel);
            openWindow(activity.getOpeningHours(), arrival, leave)
                    .ifPresent(window -> {
                        int preferenceMatches = preferredTags.isEmpty() ? 0 : (int) activity.getTags().stream()
                                .map(tag -> tag.trim().toLowerCase(Locale.ROOT))
                                .distinct()
                                .filter(preferredTags::contains)
                                .count();
                        matches.add(new Match(activity, travel, arrival, window, preferenceMatches));
                    });
        }

        return new ExploreResponse(matches.stream()
                .sorted(Comparator.comparingInt(Match::preferenceMatches).reversed()
                        .thenComparing(Match::travel))
                .limit(MAX_RESULTS)
                .map(this::toResponse)
                .toList());
    }

    /** The opening window that overlaps [arrival, leave], if any. */
    private Optional<Window> openWindow(OpeningHours hours, ZonedDateTime arrival, ZonedDateTime leave) {
        // Undated activities repeat daily; yesterday's window matters for overnight ones (22:00-05:00).
        List<LocalDate> days = hours.getDate() != null
                ? List.of(hours.getDate())
                : List.of(arrival.toLocalDate().minusDays(1), arrival.toLocalDate(), leave.toLocalDate());
        for (LocalDate day : days) {
            ZonedDateTime open = day.atTime(hours.getStart()).atZone(ZONE);
            ZonedDateTime close = day.atTime(hours.getEnd()).atZone(ZONE);
            if (!close.isAfter(open)) {
                close = close.plusDays(1);
            }
            if (open.isBefore(leave) && close.isAfter(arrival)) {
                return Optional.of(new Window(open, close));
            }
        }
        return Optional.empty();
    }

    private ExploreActivity toResponse(Match match) {
        Activity activity = match.activity();
        Window window = match.window();
        boolean event = activity.getOpeningHours().getDate() != null;
        boolean notYetOpen = window.open().isAfter(match.arrival());

        String timingLabel;
        if (event) {
            timingLabel = notYetOpen
                    ? "Beginnt um " + CLOCK.format(window.open()) + " Uhr"
                    : "Läuft bis " + CLOCK.format(window.close()) + " Uhr";
        } else {
            timingLabel = notYetOpen
                    ? "Öffnet um " + CLOCK.format(window.open()) + " Uhr"
                    : "Geöffnet bis " + CLOCK.format(window.close()) + " Uhr";
        }

        ActivityImages.ImageRef image = activityImages.imageFor(activity);

        return new ExploreActivity(
                activity.getId(),
                activity.getTitle(),
                activity.getDescription(),
                event ? "event" : "place",
                categoryLabel(activity.getCategory()),
                new Coordinates(activity.getLocation().getLat(), activity.getLocation().getLon()),
                activity.getLocation().getAddress(),
                activity.getSource() == null ? null : activity.getSource().getUrl(),
                mapsUrl(activity.getLocation()),
                event ? window.open().toOffsetDateTime().toString() : null,
                event ? window.close().toOffsetDateTime().toString() : null,
                event ? null : CLOCK.format(window.open()) + "–" + CLOCK.format(window.close()) + " Uhr",
                (int) Math.max(1, Math.round(match.travel().toSeconds() / 60.0)),
                timingLabel,
                image == null ? null : image.url(),
                image == null ? null : new ImageCredit(image.author(), image.sourceUrl(), image.license(), image.licenseUrl()));
    }

    private static String mapsUrl(Location location) {
        if (location == null || location.getLat() == null || location.getLon() == null) {
            return null;
        }
        return "https://www.google.com/maps/search/?api=1&query=" + location.getLat() + "," + location.getLon();
    }

    private static String categoryLabel(String category) {
        String label = CATEGORY_LABELS.get(category.trim().toLowerCase(Locale.ROOT));
        if (label != null) {
            return label;
        }
        return category.isEmpty() ? category : Character.toUpperCase(category.charAt(0)) + category.substring(1);
    }

    private record Window(ZonedDateTime open, ZonedDateTime close) {
    }

    private record Match(Activity activity, Duration travel, ZonedDateTime arrival, Window window,
                         int preferenceMatches) {
    }
}
