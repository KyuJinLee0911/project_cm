package com.ssafy.a203.domain.video.dto.response;

public record VideoSummary(
        Long videoId,
        String thumbnailUrl,
        Boolean isAnalyzed,
        Boolean succeeded
) {

    public static VideoSummary of(Long videoId, String thumbnailUrl, Boolean isAnalyzed,
            Boolean succeeded) {
        return new VideoSummary(videoId, thumbnailUrl, isAnalyzed, succeeded);
    }
}
