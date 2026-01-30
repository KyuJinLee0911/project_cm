package com.ssafy.a203.domain.trial.entity;

import com.ssafy.a203.domain.exerciseSession.entity.ExerciseSession;
import com.ssafy.a203.domain.trial.dto.request.CreateTrialRequest;
import com.ssafy.a203.domain.trial.dto.request.UpdateTrialRequest;
import com.ssafy.a203.domain.user.entity.User;
import com.ssafy.a203.global.common.BaseEntity;
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
@Table(name = "trials")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Trial extends BaseEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    Long id;

    @Comment("난이도")
    @Column(nullable = false)
    String difficulty;

    @Comment("세션")
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "session_id", nullable = false)
    ExerciseSession exerciseSession;

    @Comment("유저")
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    User user;

    private Trial(String difficulty, ExerciseSession session, User user) {
        this.difficulty = difficulty;
        this.exerciseSession = session;
        this.user = user;
    }

    public static Trial from(CreateTrialRequest request, ExerciseSession session, User user) {
        return new Trial(request.difficulty(), session, user);
    }

    public void updateTrial(UpdateTrialRequest request) {
        this.difficulty = request.difficulty();
    }

    public void deleteTrial() {
        this.delete();
    }
}
