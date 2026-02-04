package com.kjlee.climbmate.domain.video.entity;

import com.kjlee.climbmate.domain.exerciseSession.entity.ExerciseSession;
import com.kjlee.climbmate.domain.trial.entity.Trial;
import com.kjlee.climbmate.domain.user.entity.User;
import com.kjlee.climbmate.global.common.BaseEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.Comment;

@Entity
@Getter
@Table(name = "videos")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Video extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Comment("비디오 파일 키")
    @Column
    private String vFileKey;

    @Comment("썸네일 파일 키")
    @Column
    private String tFileKey;

    @Comment("영상 분석 세션 id")
    @Column
    private String sessionId;

    @Comment("운동한 유저")
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Comment("운동 세션")
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "exercise_session_id", nullable = false)
    private ExerciseSession exerciseSession;

    @Comment("운동 시도")
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "trial_id", nullable = false)
    private Trial trial;

    @Comment("분석 여부")
    @Column(nullable = false)
    private boolean isAnalyzed = false;


    private Video(String vFileKey, String tFileKey, User user, ExerciseSession exerciseSession,
            Trial trial) {
        this.vFileKey = vFileKey;
        this.tFileKey = tFileKey;
        this.user = user;
        this.exerciseSession = exerciseSession;
        this.trial = trial;
    }

    public static Video of(String vFileKey, String tFileKey, User user,
            ExerciseSession exerciseSession, Trial trial) {
        return new Video(vFileKey, tFileKey, user, exerciseSession, trial);
    }

    public void markAsAnalyzed() {
        isAnalyzed = true;
    }

    public void updateSessionId(String sessionId) {
        this.sessionId = sessionId;
    }

    public void deleteSessionId() {
        this.sessionId = null;
    }

    public void deleteVideo() {
        this.delete();
    }
}
