package com.ssafy.a203.domain.trial.dto.response;

import com.ssafy.a203.domain.video.dto.response.VideoSummary;
import java.util.List;

public record TrialDetailResponse(
        Long trialId,
        List<VideoSummary> videoSummaries
) {

    public static TrialDetailResponse of(Long trialId, List<VideoSummary> videoSummaries) {
        return new TrialDetailResponse(trialId, videoSummaries);
    }

}
