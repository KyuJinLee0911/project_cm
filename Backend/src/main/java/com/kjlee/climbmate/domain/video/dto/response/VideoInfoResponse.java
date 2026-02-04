package com.kjlee.climbmate.domain.video.dto.response;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record VideoInfoResponse(
        @NotNull Long videoId,
        @NotNull LocalDateTime createdAt,
        @NotNull Boolean isAnalyzed,
        @NotNull Boolean isSuccesses,
        @NotNull String thumbnailKey
) {

    public static VideoInfoResponse of(Long videoId, LocalDateTime createdAt,
            boolean isAnalyzed, boolean isSuccesses, String thumbnailKey) {
        return new VideoInfoResponse(videoId, createdAt, Boolean.TRUE.equals(isAnalyzed),
                Boolean.TRUE.equals(isSuccesses), thumbnailKey);
    }
}
