package de.muenster.aktivitaeten.routing;

import com.graphhopper.GraphHopper;
import com.graphhopper.config.Profile;
import com.graphhopper.json.Statement;
import com.graphhopper.routing.DijkstraOneToMany;
import com.graphhopper.routing.util.EdgeFilter;
import com.graphhopper.routing.util.TraversalMode;
import com.graphhopper.routing.weighting.Weighting;
import com.graphhopper.storage.index.Snap;
import com.graphhopper.util.CustomModel;
import com.graphhopper.util.PMap;
import de.muenster.aktivitaeten.activity.Activity;
import de.muenster.aktivitaeten.activity.ActivityRepository;
import jakarta.annotation.PreDestroy;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Service;

import java.nio.file.Files;
import java.nio.file.Path;
import java.io.IOException;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.stream.Collectors;

@Service
public class WalkingRouterService {
    private static final Logger log = LoggerFactory.getLogger(WalkingRouterService.class);

    private final String osmFile;
    private final String graphDirectory;
    private final ActivityRepository activityRepository;
    private GraphHopper hopper;

    public WalkingRouterService(
            @Value("${routing.osm-file:classpath:muenster-regbez.osm.pbf}") String osmFile,
            @Value("${routing.graph-directory:${java.io.tmpdir}/aktivitaeten-graph}") String graphDirectory,
            ActivityRepository activityRepository) {
        this.osmFile = osmFile;
        this.graphDirectory = graphDirectory;
        this.activityRepository = activityRepository;
    }

    public synchronized WalkingRouteResponse route(WalkingRouteRequest request) {
        GraphHopper graph = graph();
        double maximumSeconds = request.maxWalkingMinutes() * 60.0;
        List<WalkingRouteResponse.Result> results = new ArrayList<>();
        List<Activity> activities = activityRepository.findAll();

        Snap originSnap = graph.getLocationIndex().findClosest(
                request.origin().latitude(), request.origin().longitude(), EdgeFilter.ALL_EDGES);
        if (!originSnap.isValid()) {
            throw new IllegalStateException("Could not find a routable graph node for the origin");
        }

        Weighting weighting = graph.createWeighting(graph.getProfile("foot"), new PMap());
        // No setWeightLimit: DijkstraOneToMany reuses its search across targets, and once one
        // search stops at the limit every later target comes back "not found", even nearby ones.
        // The time limit is applied to the path time below instead.
        DijkstraOneToMany dijkstra = new DijkstraOneToMany(
                graph.getBaseGraph(), weighting, TraversalMode.NODE_BASED);
        int originNode = originSnap.getClosestNode();

        for (Activity activity : activities) {
            Coordinate destination = new Coordinate(
                    activity.getLocation().getLat(), activity.getLocation().getLon());
            Snap destinationSnap = graph.getLocationIndex().findClosest(
                    destination.latitude(), destination.longitude(), EdgeFilter.ALL_EDGES);
            if (!destinationSnap.isValid()) {
                continue;
            }

            com.graphhopper.routing.Path path = dijkstra.calcPath(
                    originNode, destinationSnap.getClosestNode());
            if (!path.isFound()) {
                continue;
            }

            double seconds = path.getTime() / 1000.0;
            if (seconds > maximumSeconds) {
                continue;
            }
            results.add(new WalkingRouteResponse.Result(activity.getId(), seconds));
        }
        results.sort(Comparator.comparingDouble(WalkingRouteResponse.Result::durationSeconds));
        return new WalkingRouteResponse(results);
    }

    public WalkingRouteRequest testRequest() {
        return new WalkingRouteRequest(
                new Coordinate(51.952248, 7.639208),
                30.0);
    }

    public synchronized List<String> suggest(WalkingSuggestionRequest request) {
        WalkingRouteResponse routes = route(new WalkingRouteRequest(
                request.origin(), request.maxWalkingMinutes()));
        List<String> reachableIds = routes.routes().stream()
                .map(WalkingRouteResponse.Result::activityId)
                .toList();
        if (reachableIds.isEmpty()) {
            return List.of();
        }

        List<Activity> candidates = activityRepository.findAllById(reachableIds);
        WalkingSuggestionRequest.PreferenceFilter preferences = request.preferences();
        List<Activity> filtered = candidates.stream()
                .filter(activity -> matches(activity, preferences))
                .toList();

        List<Activity> shuffled = new ArrayList<>(filtered);
        Collections.shuffle(shuffled);
        int limit = preferences != null && preferences.limit() != null
                ? Math.min(preferences.limit(), shuffled.size())
                : shuffled.size();
        return shuffled.subList(0, limit).stream()
                .map(Activity::getId)
                .toList();
    }

    private boolean matches(Activity activity, WalkingSuggestionRequest.PreferenceFilter preferences) {
        if (preferences == null) {
            return true;
        }
        if (preferences.category() != null
                && !preferences.category().equalsIgnoreCase(activity.getCategory())) {
            return false;
        }
        if (preferences.tags() != null && !preferences.tags().isEmpty()) {
            Set<String> requestedTags = preferences.tags().stream()
                    .filter(tag -> tag != null)
                    .map(tag -> tag.toLowerCase(Locale.ROOT))
                    .collect(Collectors.toSet());
            Set<String> activityTags = activity.getTags().stream()
                    .map(tag -> tag.toLowerCase(Locale.ROOT))
                    .collect(Collectors.toSet());
            if (!activityTags.containsAll(requestedTags)) {
                return false;
            }
        }
        if (preferences.groupType() != null
                && preferences.groupType() != activity.getGroupType()) {
            return false;
        }
        if (preferences.maxPriceEur() != null
                && (activity.getPriceEur() == null
                    || activity.getPriceEur() > preferences.maxPriceEur())) {
            return false;
        }
        return true;
    }

    private GraphHopper graph() {
        if (hopper != null) {
            return hopper;
        }
        Path osmPath = resolveResource(osmFile, "muenster-regbez-260924.osm.pbf");
        GraphHopper loaded = new GraphHopper()
                .setOSMFile(osmPath.toString())
                .setGraphHopperLocation(graphDirectory)
                .setEncodedValuesString("foot_average_speed")
                .setProfiles(new Profile("foot").setCustomModel(new CustomModel()
                        .addToSpeed(Statement.If("true", Statement.Op.LIMIT, "foot_average_speed"))));
        loaded.importOrLoad();
        hopper = loaded;
        return hopper;
    }

    // The first import of the OSM extract takes a while; do it in the background at startup so
    // the first request doesn't hit that. Requests block on the monitor until it's done.
    @EventListener(ApplicationReadyEvent.class)
    public void warmUpInBackground() {
        Thread warmUp = new Thread(() -> {
            try {
                loadGraph();
                log.info("Walking graph ready");
            } catch (RuntimeException exception) {
                log.warn("Walking graph could not be loaded - routing endpoints will fail: {}",
                        exception.getMessage());
            }
        }, "routing-warm-up");
        warmUp.setDaemon(true);
        warmUp.start();
    }

    private synchronized void loadGraph() {
        graph();
    }

    private Path resolveResource(String location, String resourceName) {
        if (location.startsWith("classpath:")) {
            String name = location.substring("classpath:".length());
            try (InputStream input = getClass().getClassLoader().getResourceAsStream(name)) {
                if (input == null) {
                    throw new IllegalStateException("Classpath resource not found: " + name);
                }
                Path extracted = Files.createTempFile("aktivitaeten-" + resourceName, ".data");
                Files.copy(input, extracted, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
                extracted.toFile().deleteOnExit();
                return extracted;
            } catch (IOException exception) {
                throw new IllegalStateException("Could not extract resource " + name, exception);
            }
        }
        Path path = Path.of(location);
        if (!Files.isRegularFile(path)) {
            throw new IllegalStateException("Routing file does not exist: " + path);
        }
        return path;
    }

    @PreDestroy
    public synchronized void close() {
        if (hopper != null) {
            hopper.close();
        }
    }
}
