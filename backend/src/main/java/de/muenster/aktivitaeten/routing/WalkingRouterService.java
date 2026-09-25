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
import java.util.List;

@Service
public class WalkingRouterService {
    private static final Logger log = LoggerFactory.getLogger(WalkingRouterService.class);

    private final String osmFile;
    private final String graphDirectory;
    private final String destinationsFile;
    private GraphHopper hopper;

    public WalkingRouterService(
            @Value("${routing.osm-file:classpath:muenster-regbez-260924.osm.pbf}") String osmFile,
            @Value("${routing.destinations-file:classpath:stuff.csv}") String destinationsFile,
            @Value("${routing.graph-directory:${java.io.tmpdir}/aktivitaeten-graph}") String graphDirectory) {
        this.osmFile = osmFile;
        this.destinationsFile = destinationsFile;
        this.graphDirectory = graphDirectory;
    }

    public synchronized WalkingRouteResponse route(WalkingRouteRequest request) {
        return new WalkingRouteResponse(
                routeTo(request.origin(), readDestinations(), request.maxWalkingMinutes() * 60.0));
    }

    /** One shared Dijkstra search from {@code origin}; only destinations within {@code maximumSeconds}. */
    public synchronized List<WalkingRouteResponse.Result> routeTo(
            Coordinate origin, List<Coordinate> destinations, double maximumSeconds) {
        GraphHopper graph = graph();
        List<WalkingRouteResponse.Result> results = new ArrayList<>();

        Snap originSnap = graph.getLocationIndex().findClosest(
                origin.latitude(), origin.longitude(), EdgeFilter.ALL_EDGES);
        if (!originSnap.isValid()) {
            throw new IllegalStateException("Could not find a routable graph node for the origin");
        }

        Weighting weighting = graph.createWeighting(graph.getProfile("foot"), new PMap());
        // No setWeightLimit: DijkstraOneToMany reuses its search across targets, and once one
        // search stops at the limit every later target comes back "not found", even nearby ones.
        // Reachability is decided by the path time below instead.
        DijkstraOneToMany dijkstra = new DijkstraOneToMany(
                graph.getBaseGraph(), weighting, TraversalMode.NODE_BASED);
        int originNode = originSnap.getClosestNode();

        for (Coordinate destination : destinations) {
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
            if (seconds <= maximumSeconds) {
                results.add(new WalkingRouteResponse.Result(destination, seconds));
            }
        }
        return results;
    }

    // The first import of the OSM extract takes minutes; do it in the background at startup so
    // the first explore request doesn't hit that. Requests block on the monitor until it's done.
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

    public WalkingRouteRequest testRequest() {
        return new WalkingRouteRequest(
                new Coordinate(51.952248, 7.639208),
                120.0);
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

    private List<Coordinate> readDestinations() {
        try {
            Path path = resolveResource(destinationsFile, "stuff.csv");
            return Files.readAllLines(path).stream()
                    .filter(line -> !line.isBlank())
                    .map(line -> line.split(";", -1))
                    .map(parts -> {
                        if (parts.length != 2) {
                            throw new IllegalStateException("Invalid destination row: " + String.join(";", parts));
                        }
                        return new Coordinate(
                                Double.parseDouble(parts[0].trim()),
                                Double.parseDouble(parts[1].trim()));
                    })
                    .toList();
        } catch (IOException | NumberFormatException exception) {
            throw new IllegalStateException("Could not read destinations from " + destinationsFile, exception);
        }
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
