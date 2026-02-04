package com.kjlee.climbmate.domain.exerciseSession.entity;

import com.kjlee.climbmate.domain.exerciseSession.dto.request.CreateSessionRequest;
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
import java.time.Duration;
import java.time.LocalDateTime;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.Comment;

@Entity
@Getter
@Table(name = "exercise_sessions")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class ExerciseSession extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    Long id;

    @Comment("운동 장소")
    @Column(nullable = false)
    String location;

    @Comment("세션 시작 시간")
    @Column(nullable = false)
    LocalDateTime startedAt;

    @Comment("세션 종료 시간")
    LocalDateTime endedAt;

    @Comment("총 운동 시간")
    Long duration;

    @Comment("회원")
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    User user;

    private ExerciseSession(String location, LocalDateTime startedAt, User user) {
        this.location = location;
        this.startedAt = startedAt;
        this.user = user;
    }

    public static ExerciseSession from(CreateSessionRequest request, User user) {
        return new ExerciseSession(request.location(), request.startedAt(), user);
    }

    public void setEndTime() {
        endedAt = LocalDateTime.now();
        Duration temp = Duration.between(startedAt, endedAt);
        duration = temp.toSeconds();
    }


    public void deleteSession() {
        this.delete();
    }
}
