package com.kjlee.climbmate.domain.trial.dto.response;

import com.kjlee.climbmate.domain.trial.entity.Trial;

public record TrialInfoResponse(
        Long trialId,
        String difficulty
) {

    public static TrialInfoResponse from(Trial trial) {
        return new TrialInfoResponse(trial.getId(), trial.getDifficulty());
    }
}
