package com.ssafy.a203.domain.exerciseSession.dto.response;

import com.ssafy.a203.domain.trial.dto.response.TrialInfoResponse;
import java.util.List;

public record SessionDetailResponse(
        Long sessionId,
        List<TrialInfoResponse> trials
) {

    public static SessionDetailResponse of(Long sessionId, List<TrialInfoResponse> trials) {
        return new SessionDetailResponse(sessionId, trials);
    }
}
