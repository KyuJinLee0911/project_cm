package com.ssafy.a203.domain.exerciseSession.dto.response;

import com.ssafy.a203.domain.exerciseSession.entity.ExerciseSession;
import java.time.LocalDateTime;

public record SessionInfoResponse(
        Long sessionId,
        String location,
        LocalDateTime startedAt,
        LocalDateTime endedAt,
        Long duration
) {

    public static SessionInfoResponse from(ExerciseSession session) {
        return new SessionInfoResponse(session.getId(), session.getLocation(),
                session.getStartedAt(), session.getEndedAt(), session.getDuration());
    }

}
