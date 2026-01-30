package com.ssafy.a203.domain.trial.dto.response;

import com.ssafy.a203.domain.trial.entity.Trial;

public record TrialInfoResponse(
        Long trialId,
        String difficulty
) {

    public static TrialInfoResponse from(Trial trial) {
        return new TrialInfoResponse(trial.getId(), trial.getDifficulty());
    }
}
