package com.ssafy.a203.domain.video._hold.repository;

import com.ssafy.a203.domain.video._hold.entity.Hold;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

public interface HoldRepository extends JpaRepository<Hold, Long> {

    List<Hold> findAllByVideoIdAndDeletedAtIsNull(Long videoId);

    boolean existsByVideoIdAndDeletedAtIsNull(Long videoId);

    Optional<Hold> findByIdAndDeletedAtIsNull(Long id);

    @Query("""
                UPDATE Hold h
                SET h.deletedAt = CURRENT_TIMESTAMP
                WHERE h.video.id = :videoId
            """)
    void softDeleteByVideoId(Long videoId);
}
