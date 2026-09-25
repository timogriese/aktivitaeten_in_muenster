package de.muenster.aktivitaeten.api;

import de.muenster.aktivitaeten.routing.WalkingRouteRequest;
import de.muenster.aktivitaeten.routing.WalkingRouteResponse;
import de.muenster.aktivitaeten.routing.WalkingRouterService;
import de.muenster.aktivitaeten.routing.WalkingSuggestionRequest;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/api/routing")
public class RoutingController {
    private final WalkingRouterService walkingRouterService;

    public RoutingController(WalkingRouterService walkingRouterService) {
        this.walkingRouterService = walkingRouterService;
    }

    @PostMapping("/walking")
    public WalkingRouteResponse walking(@Valid @RequestBody WalkingRouteRequest request) {
        return walkingRouterService.route(request);
    }

    @PostMapping("/walking/test")
    public WalkingRouteResponse walkingTest() {
        return walkingRouterService.route(walkingRouterService.testRequest());
    }

    @PostMapping("/suggest")
    public List<String> suggest(@Valid @RequestBody WalkingSuggestionRequest request) {
        return walkingRouterService.suggest(request);
    }
}
