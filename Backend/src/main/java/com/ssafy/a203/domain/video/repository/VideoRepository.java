package com.ssafy.a203.domain.video.repository;

import com.ssafy.a203.domain.video.dto.VideoSummaryProjection;
import com.ssafy.a203.domain.video.dto.response.VideoInfoResponse;
import com.ssafy.a203.domain.video.entity.Video;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface VideoRepository extends JpaRepository<Video, Long> {

    Optional<Video> findVideoByIdAndDeletedAtIsNull(Long videoId);

    @Query("""
            SELECT new com.ssafy.a203.domain.video.dto.response.VideoInfoResponse(
            v.id, v.createdAt, COALESCE(v.isAnalyzed, false),
            COALESCE(ei.isSuccesses, false), v.tFileKey
            )
            FROM Video v
            LEFT JOIN ExerciseInfo ei ON ei.video = v
            WHERE v.user.id = :userId
            AND v.deletedAt IS NULL
            ORDER BY v.createdAt DESC
            """)
    List<VideoInfoResponse> findAllByUserId(Long userId);

    @Query("""
            SELECT new com.ssafy.a203.domain.video.dto.response.VideoInfoResponse(
            v.id, v.createdAt, COALESCE(v.isAnalyzed, false),
            COALESCE(ei.isSuccesses, false), v.tFileKey
            )
            FROM Video v
            LEFT JOIN ExerciseInfo ei ON ei.video = v
            WHERE v.user.id = :userId
            AND CAST(v.createdAt AS date) = :date
            AND v.deletedAt IS NULL
            ORDER BY v.createdAt DESC
            """)
    List<VideoInfoResponse> findAllByUserIdAndCreatedAtBetween(Long userId, LocalDate date);

    List<Video> findAllByExerciseSessionIdAndDeletedAtIsNull(Long sessionId);

    List<Video> findAllByTrialIdAndDeletedAtIsNull(Long trialId);

    @Query("""
                    SELECT new com.ssafy.a203.domain.video.dto.VideoSummaryProjection(
                    v.id, v.tFileKey, v.isAnalyzed, ei.isSuccesses
                    )
                    FROM Video v
                    JOIN ExerciseInfo ei ON ei.video.id = v.id
                    WHERE v.trial.id = :trialId
                    AND v.deletedAt IS NULL
                    AND ei.deletedAt IS NULL
            """)
    List<VideoSummaryProjection> findSummaryByTrialId(@Param("trialId") Long trialId);
}
