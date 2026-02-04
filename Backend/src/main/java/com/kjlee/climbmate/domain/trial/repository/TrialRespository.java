package com.kjlee.climbmate.domain.trial.repository;

import com.kjlee.climbmate.domain.trial.entity.Trial;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface TrialRespository extends JpaRepository<Trial, Long> {

    Optional<Trial> findByIdAndDeletedAtIsNull(Long id);

    List<Trial> findByExerciseSessionIdAndDeletedAtIsNull(Long exerciseSessionId);
}
