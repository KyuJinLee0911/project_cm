package com.kjlee.climbmate.domain.video.dto.response;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record VideoDetailResponse(
        @NotNull Long id,
        @NotBlank String videoUrl,
        @NotNull boolean isAnalyzed
) {

    public static VideoDetailResponse of(Long id, String videoUrl, boolean isAnalyzed) {
        return new VideoDetailResponse(id, videoUrl, isAnalyzed);
    }
}
