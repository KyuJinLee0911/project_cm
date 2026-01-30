package com.ssafy.a203.domain.exerciseInfo.repository;

import com.ssafy.a203.domain.exerciseInfo.entity.ExerciseInfo;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

public interface ExerciseInfoRepository extends JpaRepository<ExerciseInfo, Long> {

    Optional<ExerciseInfo> findByVideoIdAndDeletedAtIsNull(Long videoId);

    @Query("""
                UPDATE ExerciseInfo ei
                SET ei.deletedAt = CURRENT_TIMESTAMP
                WHERE ei.video.id = :videoId
            """)
    void softDeleteByVideoId(Long videoId);
}
