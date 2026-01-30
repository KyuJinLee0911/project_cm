package com.ssafy.a203.domain.video.dto;

public record VideoSummaryProjection(
        Long videoId,
        String thumbnailUrl,
        Boolean isAnalyzed,
        Boolean succeeded
) {

}
