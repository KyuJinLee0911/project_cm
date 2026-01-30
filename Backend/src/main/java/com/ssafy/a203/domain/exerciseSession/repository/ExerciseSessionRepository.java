package com.ssafy.a203.domain.exerciseSession.repository;

import com.ssafy.a203.domain.exerciseSession.entity.ExerciseSession;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ExerciseSessionRepository extends JpaRepository<ExerciseSession, Long> {


    Optional<ExerciseSession> findByIdAndDeletedAtIsNull(Long id);

    List<ExerciseSession> findAllByUserIdAndDeletedAtIsNull(Long userId);
}
