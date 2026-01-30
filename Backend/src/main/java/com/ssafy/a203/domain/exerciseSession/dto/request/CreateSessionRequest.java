package com.ssafy.a203.domain.exerciseSession.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record CreateSessionRequest(
        @NotBlank
        @Schema(description = "운동 장소", example = "더클라임 강남점")
        String location,
        @NotNull
        @Schema(description = "세션 시작 시간", example = "2025-11-13T11:12:37")
        LocalDateTime startedAt
) {

}
