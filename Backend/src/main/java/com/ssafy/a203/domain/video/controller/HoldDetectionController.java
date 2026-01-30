package com.ssafy.a203.domain.video.controller;

import com.ssafy.a203.domain.video._hold.dto.request.HoldDetectionRequest;
import com.ssafy.a203.domain.video._hold.dto.response.HoldInfoResponse;
import com.ssafy.a203.domain.video._hold.dto.response.SessionOpenResponse;
import com.ssafy.a203.domain.video.service.AIHoldService;
import com.ssafy.a203.global.common.dto.ApiResponse;
import com.ssafy.a203.global.security.dto.CustomUserDetails;
import io.swagger.v3.oas.annotations.Operation;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RequestPart;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/videos/{video_id}/holds/detect")
public class HoldDetectionController {

    private final AIHoldService aiHoldService;

    @PostMapping(
            value = "/open",
            consumes = MediaType.MULTIPART_FORM_DATA_VALUE
    )
    @Operation(summary = "홀드 인식 세션 open",
            description = "홀드 인식을 시작하기 위한 홀드 인식 세션을 열고, 세션 id를 반환합니다. "
                    + "홀드 인식을 하기 위해 필요한 이미지를 첨부해야 합니다.")
    public ResponseEntity<ApiResponse<SessionOpenResponse>> openSession(
            @PathVariable("video_id") Long videoId,
            @RequestPart("file") MultipartFile file,
            @AuthenticationPrincipal CustomUserDetails customUserDetails
    ) {
        SessionOpenResponse response = aiHoldService.createSession(videoId, file,
                customUserDetails);
        return ApiResponse.created(response);
    }

    @PostMapping
    @Operation(summary = "홀드 인식",
            description = "AI 서버에 요청을 보내 홀드를 인식합니다. "
                    + "마지막 요청일 경우, request param에 last를 true로 넣어 마지막 요청임을 알리고, 세션을 닫습니다.")
    public ResponseEntity<ApiResponse<HoldInfoResponse>> detectHolds(
            @PathVariable("video_id") Long video_id,
            @RequestBody HoldDetectionRequest request,
            @RequestParam("last") boolean isLast,
            @AuthenticationPrincipal CustomUserDetails customUserDetails
    ) {
        HoldInfoResponse response = aiHoldService.detectHolds(request, video_id, isLast,
                customUserDetails);
        return ApiResponse.ok(response);
    }

    @DeleteMapping("/{hold_id}")
    @Operation(summary = "홀드 인식 단일 취소",
            description = "선택한 홀드의 인식을 취소합니다. "
                    + "holdId가 일치하는 홀드를 삭제처리합니다.")
    public ResponseEntity<ApiResponse<Void>> deleteHold(
            @PathVariable("video_id") Long video_id,
            @PathVariable("hold_id") Long hold_id,
            @AuthenticationPrincipal CustomUserDetails customUserDetails
    ) {
        aiHoldService.deleteHold(video_id, hold_id, customUserDetails);
        return ApiResponse.ok();
    }

    @DeleteMapping
    @Operation(summary = "홀드 인식 취소",
            description = "홀드 인식을 취소합니다. "
                    + "취소 요청이 들어오면, 인식하고 저장했던 모든 홀드 정보를 삭제한 후 세션을 닫고 video에서 sessionId를 삭제합니다.")
    public ResponseEntity<ApiResponse<Void>> cancleHoldDetection(
            @PathVariable("video_id") Long video_id,
            @AuthenticationPrincipal CustomUserDetails customUserDetails
    ) {
        aiHoldService.removeAndCloseSession(video_id, customUserDetails);
        return ApiResponse.ok();
    }
}
