package com.kjlee.climbmate.domain.video.dto;

public record VideoSummaryProjection(
        Long videoId,
        String thumbnailUrl,
        Boolean isAnalyzed,
        Boolean succeeded
) {

}
