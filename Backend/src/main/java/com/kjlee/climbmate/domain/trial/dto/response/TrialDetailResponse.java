package com.kjlee.climbmate.domain.trial.dto.response;

import com.kjlee.climbmate.domain.video.dto.response.VideoSummary;
import java.util.List;

public record TrialDetailResponse(
        Long trialId,
        List<VideoSummary> videoSummaries
) {

    public static TrialDetailResponse of(Long trialId, List<VideoSummary> videoSummaries) {
        return new TrialDetailResponse(trialId, videoSummaries);
    }

}
