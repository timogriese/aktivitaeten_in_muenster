package de.muenster.aktivitaeten.api;

import de.muenster.aktivitaeten.explore.ExploreRequest;
import de.muenster.aktivitaeten.explore.ExploreResponse;
import de.muenster.aktivitaeten.explore.ExploreService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/explore")
public class ExploreController {
    private final ExploreService exploreService;

    public ExploreController(ExploreService exploreService) {
        this.exploreService = exploreService;
    }

    @PostMapping
    public ExploreResponse explore(@Valid @RequestBody ExploreRequest request) {
        return exploreService.explore(request);
    }

    @GetMapping("/{id}")
    public ExploreResponse.ExploreActivity get(@PathVariable String id) {
        return exploreService.getActivity(id);
    }
}
