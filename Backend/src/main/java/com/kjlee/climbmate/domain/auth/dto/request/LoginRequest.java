package com.kjlee.climbmate.domain.auth.dto.request;

import com.kjlee.climbmate.global.validation.annotation.ValidPassword;
import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.Size;

public record LoginRequest(

        @Email @Size(max=40)
        @Schema(description = "이메일", example = "abc123@email.com")
        String email,
        @ValidPassword
        @Schema(description = "비밀번호", example = "1q2w3e4r!")
        String password
) {

}
