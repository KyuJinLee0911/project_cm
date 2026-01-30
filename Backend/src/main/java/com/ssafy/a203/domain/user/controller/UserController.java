package com.ssafy.a203.domain.user.controller;

import com.ssafy.a203.domain.user.dto.request.SignUpRequest;
import com.ssafy.a203.domain.user.dto.request.UpdateUserRequest;
import com.ssafy.a203.domain.user.dto.response.UserInfoResponse;
import com.ssafy.a203.domain.user.service.UserService;
import com.ssafy.a203.global.common.dto.ApiResponse;
import com.ssafy.a203.global.security.dto.CustomUserDetails;
import io.swagger.v3.oas.annotations.Operation;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/users")
public class UserController {
    private final UserService userService;

    @PostMapping("")
    @Operation(summary = "회원가입", description = "회원가입 API 입니다.")
    public ResponseEntity<ApiResponse<Void>> signup(
            @RequestBody @Valid SignUpRequest request
    ){
        userService.signUp(request);
        return ApiResponse.created();
    }

    @PutMapping("")
    @Operation(summary = "회원 정보 수정", description = "회원 정보 수정 API 입니다. 수정 가능한 정보는 닉네임, 키, 몸무게, 팔 길이가 있습니다.")
    public ResponseEntity<ApiResponse<UserInfoResponse>> updateUserInfo(
            @RequestBody @Valid UpdateUserRequest request,
            @AuthenticationPrincipal CustomUserDetails customUserDetails
    ){
        UserInfoResponse response = userService.updateUserInfo(request, customUserDetails);
        return ApiResponse.ok(response);
    }

    @GetMapping("")
    @Operation(summary = "회원 정보 조회", description = "회원 정보 조회 API 입니다.")
    public ResponseEntity<ApiResponse<UserInfoResponse>> getUserInfo(
            @AuthenticationPrincipal CustomUserDetails customUserDetails
    ) {
        UserInfoResponse response = userService.getUser(customUserDetails);
        return ApiResponse.ok(response);
    }

    @GetMapping("/email")
    @Operation(summary = "이메일 중복 확인", description = "이메일 중복 확인 API 입니다.")
    public ResponseEntity<ApiResponse<Void>> checkEmail(
            @RequestParam String email
    ){
        userService.checkEmail(email);
        return ApiResponse.ok();
    }

    @DeleteMapping("")
    @Operation(summary = "회원 탈퇴", description = "회원 탈퇴 API 입니다.")
    public ResponseEntity<ApiResponse<Void>> withdrawal(
            @AuthenticationPrincipal CustomUserDetails customUserDetails
    ) {
        userService.withdraw(customUserDetails);
        return ApiResponse.ok();
    }
}
