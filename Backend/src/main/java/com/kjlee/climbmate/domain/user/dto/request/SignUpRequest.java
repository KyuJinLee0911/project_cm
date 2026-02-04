package com.kjlee.climbmate.domain.user.dto.request;

import com.kjlee.climbmate.global.validation.annotation.ValidPassword;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record SignUpRequest(
        @Email @Size(max=40)
        @Schema(description = "이메일", example = "abc123@email.com")
        String email,

        @ValidPassword
        @Schema(description = "비밀번호", example = "1q2w3e4r!")
        String password,
        @NotBlank @Size(min = 2, max = 20)
        @Schema(description = "닉네임", example = "클라임의황제")
        String nickname,
        @NotNull
        @Schema(description = "키", example = "182.5")
        Float height,
        @NotNull
        @Schema(description = "몸무게", example = "92.7")
        Float weight,
        @Schema(description = "팔 길이", example = "300")
        Float reach
) {

}
