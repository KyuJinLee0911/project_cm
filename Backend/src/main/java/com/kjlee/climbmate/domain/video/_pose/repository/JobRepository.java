package com.kjlee.climbmate.domain.video._pose.repository;

import com.kjlee.climbmate.domain.video._pose.entity.AnalyzedData;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;

public interface JobRepository extends JpaRepository<AnalyzedData, String> {

    Optional<AnalyzedData> findByIdAndDeletedAtIsNull(String id);

    Optional<AnalyzedData> findByVideoIdAndDeletedAtIsNull(Long videoId);

    @Modifying
    @Query("UPDATE AnalyzedData ad SET ad.status = :status WHERE ad.id = :jobId")
    void updateStatus(String jobId, String status);

    @Query("""
                UPDATE AnalyzedData ad
                SET ad.deletedAt = CURRENT_TIMESTAMP
                WHERE ad.video.id = :videoId
            """)
    void softDeleteByVideoId(Long videoId);

}
