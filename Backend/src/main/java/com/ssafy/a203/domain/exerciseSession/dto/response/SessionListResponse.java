package com.ssafy.a203.domain.exerciseSession.dto.response;

import java.util.List;

public record SessionListResponse(
        List<SessionInfoResponse> sessions
) {

    public static SessionListResponse of(List<SessionInfoResponse> sessions) {
        return new SessionListResponse(sessions);
    }

}
