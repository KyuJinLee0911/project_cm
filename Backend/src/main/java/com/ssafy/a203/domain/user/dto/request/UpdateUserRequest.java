package com.ssafy.a203.domain.user.dto.request;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record UpdateUserRequest(
        @NotBlank
        @Schema(description = "닉네임", example = "클라임의신")
        String nickname,
        @NotNull
        @Schema(description = "키", example = "182.4")
        Float height,
        @NotNull
        @Schema(description = "몸무게", example = "92.7")
        Float weight,
        @Schema(description = "팔 길이", example = "300")
        Float reach
) {

}
