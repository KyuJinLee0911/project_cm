package com.ssafy.a203.domain.exerciseSession.controller;

import com.ssafy.a203.domain.exerciseSession.dto.request.CreateSessionRequest;
import com.ssafy.a203.domain.exerciseSession.dto.response.SessionDetailResponse;
import com.ssafy.a203.domain.exerciseSession.dto.response.SessionInfoResponse;
import com.ssafy.a203.domain.exerciseSession.dto.response.SessionListResponse;
import com.ssafy.a203.domain.exerciseSession.service.ExerciseSessionService;
import com.ssafy.a203.global.common.dto.ApiResponse;
import com.ssafy.a203.global.security.dto.CustomUserDetails;
import io.swagger.v3.oas.annotations.Operation;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/sessions")
public class ExerciseSessionController {

    private final ExerciseSessionService sessionService;

    @GetMapping("/{session_id}")
    @Operation(summary = "세션 상세 정보 요청",
            description = "세션의 상세 정보(속한 trial들의 id, 난이도)를 불러오는 API입니다.")
    public ResponseEntity<ApiResponse<SessionDetailResponse>> getSessionDetail(
            @PathVariable("session_id") Long sessionId,
            @AuthenticationPrincipal CustomUserDetails customUserDetails
    ) {
        SessionDetailResponse response = sessionService.getSessionDetail(sessionId,
                customUserDetails);
        return ApiResponse.ok(response);
    }

    @GetMapping
    @Operation(summary = "세션 목록 요청",
            description = "세션 목록을 불러오는 API입니다.")
    public ResponseEntity<ApiResponse<SessionListResponse>> getSessionList(
            @AuthenticationPrincipal CustomUserDetails customUserDetails
    ) {
        SessionListResponse response = sessionService.getSessionList(customUserDetails);
        return ApiResponse.ok(response);
    }

    @PostMapping
    @Operation(summary = "세션 생성 요청",
            description = "세션을 생성하는 API 입니다. 운동 장소와 세션 시작 시간을 Request에 담아 보냅니다.")
    public ResponseEntity<ApiResponse<SessionInfoResponse>> createSession(
            @RequestBody @Valid CreateSessionRequest request,
            @AuthenticationPrincipal CustomUserDetails customUserDetails
    ) {
        SessionInfoResponse response = sessionService.createSession(request, customUserDetails);
        return ApiResponse.created(response);
    }

    @PutMapping("{session_id}")
    @Operation(summary = "세션 수정 요청",
            description = "세션의 종료 시각을 현재 시각으로 설정하고, 시작 시간과 종료 시간 사이의 duration을 계산해 업데이트 합니다. "
                    + "로직은 백엔드 서버에 전부 있으니 body에 따로 담아 보낼 내용은 없습니다.")
    public ResponseEntity<ApiResponse<SessionInfoResponse>> updateSession(
            @PathVariable("session_id") Long sessionId,
            @AuthenticationPrincipal CustomUserDetails customUserDetails
    ) {
        SessionInfoResponse response = sessionService.updateExerciseSession(sessionId,
                customUserDetails);
        return ApiResponse.ok(response);
    }

    @DeleteMapping("{session_id}")
    @Operation(summary = "세션 삭제 요청",
            description = "세션을 삭제하는 API입니다.")
    public ResponseEntity<ApiResponse<Void>> deleteSession(
            @PathVariable("session_id") Long sessionId,
            @AuthenticationPrincipal CustomUserDetails customUserDetails
    ) {
        sessionService.deleteSession(sessionId, customUserDetails);
        return ApiResponse.ok();
    }
}
