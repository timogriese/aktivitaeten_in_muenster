package de.muenster.aktivitaeten.activity;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.persistence.CollectionTable;
import jakarta.persistence.Column;
import jakarta.persistence.ElementCollection;
import jakarta.persistence.Entity;
import jakarta.persistence.Embedded;
import jakarta.persistence.Convert;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OrderColumn;
import jakarta.persistence.Table;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "activities")
public class Activity {
    private static final ZoneId ZONE = ZoneId.of("Europe/Berlin");

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(length = 36, nullable = false, updatable = false)
    private String id;

    @Column(nullable = false)
    private String title;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String description;

    @Column(nullable = false)
    private String category;

    @ElementCollection
    @CollectionTable(name = "activity_tags", joinColumns = @JoinColumn(name = "activity_id"))
    @OrderColumn(name = "tag_order")
    @Column(name = "tag", nullable = false)
    private List<String> tags = new ArrayList<>();

    @Embedded
    private Location location;

    @Convert(converter = GroupTypeConverter.class)
    @Column(name = "group_type", nullable = false)
    private GroupType groupType;

    @Embedded
    private OpeningHours openingHours;

    @Column(name = "price_eur", nullable = false)
    private Double priceEur;

    @Embedded
    private ActivitySource source;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    protected Activity() {
    }

    public Activity(String title, String description, String category, List<String> tags,
                    Location location, GroupType groupType, OpeningHours openingHours,
                    Double priceEur, ActivitySource source) {
        this.title = title;
        this.description = description;
        this.category = category;
        this.tags = new ArrayList<>(tags);
        this.location = location;
        this.groupType = groupType;
        this.openingHours = openingHours;
        this.priceEur = priceEur;
        this.source = source;
    }

    public void update(String title, String description, String category, List<String> tags,
                       Location location, GroupType groupType, OpeningHours openingHours,
                       Double priceEur, ActivitySource source) {
        this.title = title;
        this.description = description;
        this.category = category;
        this.tags = new ArrayList<>(tags);
        this.location = location;
        this.groupType = groupType;
        this.openingHours = openingHours;
        this.priceEur = priceEur;
        this.source = source;
    }

    @jakarta.persistence.PrePersist
    void onCreate() {
        LocalDateTime now = LocalDateTime.now(ZONE);
        createdAt = now;
        updatedAt = now;
    }

    @jakarta.persistence.PreUpdate
    void onUpdate() {
        updatedAt = LocalDateTime.now(ZONE);
    }

    public String getId() {
        return id;
    }

    public String getTitle() {
        return title;
    }

    public String getDescription() {
        return description;
    }

    public String getCategory() {
        return category;
    }

    public List<String> getTags() {
        return List.copyOf(tags);
    }

    public Location getLocation() {
        return location;
    }

    @JsonProperty("group_type")
    public GroupType getGroupType() {
        return groupType;
    }

    @JsonProperty("opening_hours")
    public OpeningHours getOpeningHours() {
        return openingHours;
    }

    @JsonProperty("price_eur")
    public Double getPriceEur() {
        return priceEur;
    }

    public ActivitySource getSource() {
        return source;
    }

    @JsonProperty("created_at")
    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    @JsonProperty("updated_at")
    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }
}
