package de.muenster.aktivitaeten.activity;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import java.util.List;
import java.util.Optional;

public interface ActivityRepository extends JpaRepository<Activity, String> {
    Optional<Activity> findByTitleIgnoreCase(String title);

    @Query("select a from Activity a left join fetch a.tags")
    List<Activity> findAllWithTags();
}
