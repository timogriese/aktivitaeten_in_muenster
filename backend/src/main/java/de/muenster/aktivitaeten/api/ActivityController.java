package de.muenster.aktivitaeten.api;

import com.fasterxml.jackson.annotation.JsonProperty;
import de.muenster.aktivitaeten.activity.*;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PositiveOrZero;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

import java.net.URI;
import java.util.List;

import static org.springframework.http.HttpStatus.NOT_FOUND;

@RestController
@RequestMapping("/activities")
public class ActivityController {
    private final ActivityRepository activityRepository;

    public ActivityController(ActivityRepository activityRepository) {
        this.activityRepository = activityRepository;
    }

    @GetMapping
    public List<Activity> list() {
        return activityRepository.findAllWithTags();
    }

    @PostMapping
    public ResponseEntity<Activity> createOrUpdate(@Valid @RequestBody ActivityRequest request) {
        Activity activity = activityRepository.findByTitleIgnoreCase(request.title().trim())
                .orElse(null);
        boolean created = activity == null;
        if (created) {
            activity = new Activity(request.title(), request.description(), request.category(),
                    request.tags(), request.location(), request.groupType(), request.openingHours(),
                    request.priceEur(), request.source());
        } else {
            activity.update(request.title(), request.description(), request.category(), request.tags(),
                    request.location(), request.groupType(), request.openingHours(), request.priceEur(),
                    request.source());
        }

        Activity saved = activityRepository.save(activity);
        if (!created) {
            return ResponseEntity.ok(saved);
        }
        return ResponseEntity.created(URI.create("/activities/" + saved.getId())).body(saved);
    }

    @GetMapping("/{id}")
    public Activity get(@PathVariable String id) {
        return findActivity(id);
    }

    @PutMapping("/{id}")
    public Activity update(@PathVariable String id,
                           @Valid @RequestBody ActivityUpdateRequest request) {
        Activity activity = findActivity(id);
        activity.update(
                request.title() == null ? activity.getTitle() : request.title(),
                request.description() == null ? activity.getDescription() : request.description(),
                request.category() == null ? activity.getCategory() : request.category(),
                request.tags() == null ? activity.getTags() : request.tags(),
                request.location() == null ? activity.getLocation() : request.location(),
                request.groupType() == null ? activity.getGroupType() : request.groupType(),
                request.openingHours() == null ? activity.getOpeningHours() : request.openingHours(),
                request.priceEur() == null ? activity.getPriceEur() : request.priceEur(),
                request.source() == null ? activity.getSource() : request.source());
        return activityRepository.save(activity);
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable String id) {
        if (!activityRepository.existsById(id)) {
            throw new ResponseStatusException(NOT_FOUND, "Activity not found");
        }
        activityRepository.deleteById(id);
        return ResponseEntity.noContent().build();
    }

    private Activity findActivity(String id) {
        return activityRepository.findById(id)
                .orElseThrow(() -> new ResponseStatusException(NOT_FOUND, "Activity not found"));
    }

    public record ActivityRequest(
            @NotBlank String title,
            @NotBlank String description,
            @NotBlank String category,
            @NotNull List<String> tags,
            @NotNull @Valid Location location,
            @NotNull @JsonProperty("group_type") GroupType groupType,
            @NotNull @Valid @JsonProperty("opening_hours") OpeningHours openingHours,
            @NotNull @PositiveOrZero @JsonProperty("price_eur") Double priceEur,
            @NotNull @Valid ActivitySource source) {
    }

    public record ActivityUpdateRequest(
            String title,
            String description,
            String category,
            List<String> tags,
            @Valid Location location,
            @JsonProperty("group_type") GroupType groupType,
            @Valid @JsonProperty("opening_hours") OpeningHours openingHours,
            @PositiveOrZero @JsonProperty("price_eur") Double priceEur,
            @Valid ActivitySource source) {
    }
}
