package com.ssafy.a203.domain.video._hold.dto.response;

import jakarta.validation.constraints.NotBlank;

public record SessionOpenResponse(
        @NotBlank String sessionId

) {

    public static SessionOpenResponse of(String sessionId) {
        return new SessionOpenResponse(sessionId);
    }
}
