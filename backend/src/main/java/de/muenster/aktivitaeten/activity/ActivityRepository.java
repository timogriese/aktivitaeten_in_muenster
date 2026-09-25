package de.muenster.aktivitaeten.activity;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.UUID;
import java.util.Optional;

public interface ActivityRepository extends JpaRepository<Activity, UUID> {
    Optional<Activity> findByTitleIgnoreCase(String title);
}
