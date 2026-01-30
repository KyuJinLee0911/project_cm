package com.ssafy.a203.domain.auth.service;

import com.ssafy.a203.domain.auth.dto.request.LoginRequest;
import com.ssafy.a203.domain.auth.dto.request.ReissueRequest;
import com.ssafy.a203.domain.auth.dto.response.TokenResponse;
import com.ssafy.a203.domain.user.entity.User;
import com.ssafy.a203.domain.user.service.UserReader;
import com.ssafy.a203.global.security.dto.CustomUserDetails;
import com.ssafy.a203.global.security.exception.InvalidTokenException;
import com.ssafy.a203.global.security.service.RedisRefreshTokenServices;
import com.ssafy.a203.global.security.util.JwtProvider;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuthService {

    private final JwtProvider jwtProvider;
    private final AuthenticationManager authenticationManager;
    private final RedisRefreshTokenServices redisRefreshTokenServices;
    private final UserReader userReader;

    // 로그인
    public TokenResponse login(LoginRequest request) {
        // Authentication 객체 생성
        UsernamePasswordAuthenticationToken token = new UsernamePasswordAuthenticationToken(
                request.email(), request.password());
        // 확인
        Authentication authentication = authenticationManager.authenticate(token);

        // 인증 성공
        CustomUserDetails userDetails = (CustomUserDetails) authentication.getPrincipal();

        // JWT 토큰 생성
        String accessToken = jwtProvider.generateAccessToken(userDetails);
        long accessTokenExpirationTime = jwtProvider.getExpirationTime(accessToken);
        String refreshToken = jwtProvider.generateRefreshToken(userDetails);
        long refreshTokenExpirationTime = jwtProvider.getExpirationTime(refreshToken);

        // redis에 토큰 저장
        redisRefreshTokenServices.store(userDetails.email(), refreshToken,
                refreshTokenExpirationTime);

        return TokenResponse.of(accessToken, accessTokenExpirationTime, refreshToken,
                refreshTokenExpirationTime);
    }

    // 로그아웃
    public void logout(String accessToken) {
        if (!jwtProvider.validateToken(accessToken)) {
            throw new InvalidTokenException();
        }

        // 토큰에서 사용자 정보 추출
        String email = jwtProvider.getEmail(accessToken);

        // refresh 토큰 삭제
        redisRefreshTokenServices.delete(email);

        // accessToken 남은 시간 동안 블랙리스트 등록
        long remainingTime = jwtProvider.getRemainTime(accessToken);
        redisRefreshTokenServices.setBlacklist(accessToken, remainingTime);
    }

    public TokenResponse reissue(ReissueRequest request) {
        String oldrefresh = request.refreshToken();

        if (!jwtProvider.validateToken(oldrefresh)) {
            throw new InvalidTokenException();
        }
        String userEmail = jwtProvider.getEmail(oldrefresh);
        ;
        String savedRefreshToken = redisRefreshTokenServices.get(userEmail);

        if (savedRefreshToken == null) {
            throw new InvalidTokenException();
        }

        User user = userReader.getUserByEmail(userEmail);

        CustomUserDetails details = CustomUserDetails.from(user);

        String newAccessToken = jwtProvider.generateAccessToken(details);
        long accessTokenExpirationTime = jwtProvider.getExpirationTime(newAccessToken);
        String newRefreshToken = jwtProvider.generateRefreshToken(details);
        long refreshTokenExpirationTime = jwtProvider.getExpirationTime(newRefreshToken);
        redisRefreshTokenServices.store(userEmail, newRefreshToken,
                refreshTokenExpirationTime);

        return TokenResponse.of(newAccessToken, accessTokenExpirationTime, newRefreshToken,
                refreshTokenExpirationTime);
    }

}
