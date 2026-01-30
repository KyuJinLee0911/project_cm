package com.ssafy.a203.domain.auth.controller;

import com.ssafy.a203.domain.auth.dto.request.LoginRequest;
import com.ssafy.a203.domain.auth.dto.request.ReissueRequest;
import com.ssafy.a203.domain.auth.dto.response.TokenResponse;
import com.ssafy.a203.domain.auth.service.AuthService;
import com.ssafy.a203.global.common.dto.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestHeader;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/auth")
@Tag(name = "Auth", description = "회원 인증 관련 API")
public class AuthController {

    private final AuthService authService;

    @PostMapping("/login")
    @Operation(summary = "로그인", description = "로그인 API 입니다")
    public ResponseEntity<ApiResponse<TokenResponse>> login(
            @RequestBody @Valid LoginRequest request
    ) {
        log.info(request.toString());
        TokenResponse response = authService.login(request);
        return ApiResponse.ok(response);
    }

    @PostMapping("/logout")
    @Operation(summary = "로그아웃", description = "로그아웃 API 입니다.")
    public ResponseEntity<ApiResponse<Void>> logout(
            @RequestHeader("Authorization") String authorizationHeader) {
        String token = authorizationHeader.substring(7);

        authService.logout(token);
        return ApiResponse.ok();
    }

    @PostMapping("/reissue")
    @Operation(summary = "토큰 재발급", description = "현재 보유중인 refresh token을 활용해 access token을 재발급받습니다.")
    public ResponseEntity<ApiResponse<TokenResponse>> reissue(
            @RequestBody ReissueRequest request
    ) {
        TokenResponse response = authService.reissue(request);
        return ApiResponse.ok(response);
    }
}
