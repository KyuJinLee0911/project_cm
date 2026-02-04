package com.kjlee.climbmate.domain.auth.dto.response;

public record TokenResponse(
        String accessToken,
        long accessTokenExpirationTime,
        String refreshToken,
        long refreshTokenExpirationTime
) {
    public static TokenResponse of(String accessToken, long accessTokenExpirationTime,
            String refreshToken, long refreshTokenExpirationTime){
        return new TokenResponse(accessToken, accessTokenExpirationTime, refreshToken, refreshTokenExpirationTime);
    }
}
