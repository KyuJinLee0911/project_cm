package com.ssafy.a203.domain.exerciseInfo.entity;

import com.ssafy.a203.domain.video.entity.Video;
import com.ssafy.a203.global.common.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;
import java.time.LocalDateTime;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.Comment;

@Entity
@Getter
@Table(name = "exercise_infos")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class ExerciseInfo extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Comment("운동 시작 시간")
    @Column(nullable = false)
    private LocalDateTime startedAt;

    @Comment("운동 종료 시간")
    @Column(nullable = false)
    private LocalDateTime endedAt;

    @Comment("운동 성공 여부")
    @Column(nullable = false)
    private boolean isSuccesses = false;

    @Comment("원본 영상")
    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "video_id", nullable = false)
    Video video;

    private ExerciseInfo(LocalDateTime startedAt, LocalDateTime endedAt,
            boolean isSuccesses, Video video) {
        this.startedAt = startedAt;
        this.endedAt = endedAt;
        this.isSuccesses = isSuccesses;
        this.video = video;
    }

    public static ExerciseInfo of(LocalDateTime startedAt, LocalDateTime endedAt,
            boolean isSuccesses, Video video) {
        return new ExerciseInfo(startedAt, endedAt, isSuccesses, video);
    }

    public void markAsSuccessed() {
        isSuccesses = true;
    }

}
