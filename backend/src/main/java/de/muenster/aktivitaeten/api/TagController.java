package de.muenster.aktivitaeten.api;

import de.muenster.aktivitaeten.activity.TagCatalog;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/tags")
public class TagController {
    private final TagCatalog tagCatalog;

    public TagController(TagCatalog tagCatalog) {
        this.tagCatalog = tagCatalog;
    }

    @GetMapping
    public Map<String, List<String>> tags() {
        return tagCatalog.groups();
    }
}
