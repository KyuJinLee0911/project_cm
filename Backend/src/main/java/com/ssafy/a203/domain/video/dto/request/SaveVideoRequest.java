package com.ssafy.a203.domain.video.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

public record SaveVideoRequest(
        @NotNull
        @Schema(description = "세션 id", example = "1")
        Long sessionId,
        @NotNull
        @Schema(description = "시도 id", example = "1")
        Long trialId,
        @NotBlank
        @Schema(description = "운동 장소", example = "더클라임 신사점")
        String location,
        @NotBlank
        @Schema(description = "파일 키 - Presigned URL 요청 시 받았던 file key. UUID_파일이름 형식"
                , example = "20251110_162756457_analyze.mp4")
        String vFileKey,
        @NotBlank
        @Schema(description = "썸네일 파일 키", example = "20251110_162756457_analyze.jpg")
        String tFileKey,

        @NotNull
        @Schema(description = "운동 시작 시간", example = "2025-11-10T09:38:36")
        LocalDateTime startedAt,

        @NotNull
        @Schema(description = "운동 종료 시간", example = "2025-11-10T09:39:36")
        LocalDateTime endedAt,

        @NotNull
        @Schema(description = "운동 성공 여부", example = "true")
        Boolean isSuccesses

) {

}
