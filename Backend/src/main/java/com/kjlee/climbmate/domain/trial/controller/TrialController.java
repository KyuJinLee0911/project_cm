package com.kjlee.climbmate.domain.trial.controller;

import com.kjlee.climbmate.domain.trial.dto.request.CreateTrialRequest;
import com.kjlee.climbmate.domain.trial.dto.request.UpdateTrialRequest;
import com.kjlee.climbmate.domain.trial.dto.response.TrialDetailResponse;
import com.kjlee.climbmate.domain.trial.dto.response.TrialInfoResponse;
import com.kjlee.climbmate.domain.trial.service.TrialService;
import com.kjlee.climbmate.global.common.dto.ApiResponse;
import com.kjlee.climbmate.global.security.dto.CustomUserDetails;
import io.swagger.v3.oas.annotations.Operation;
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
@RequestMapping("/api/v1/sessions/{session_id}/trials")
public class TrialController {

    private final TrialService trialService;

    @GetMapping("/{trial_id}")
    @Operation(summary = "트라이얼 상세 정보 요청",
            description = "트라이얼의 상세 정보를 불러오는 API입니다. "
                    + "불러오는 정보로는 트라이얼의 id와 트라이얼에 속한 모든 영상의 정보(영상 id, 썸네일 다운로드 주소, 분석 여부) 와 "
                    + "해당 영상과 연관된 운동 정보(성공 여부)를 dto에 담아 해당 dto들을 리스트로 불러옵니다.")
    public ResponseEntity<ApiResponse<TrialDetailResponse>> getTrialDetail(
            @PathVariable("session_id") Long sessionId,
            @PathVariable("trial_id") Long trialId,
            @AuthenticationPrincipal CustomUserDetails customUserDetails
    ) {
        TrialDetailResponse response = trialService.getTrialDetail(sessionId, trialId,
                customUserDetails);
        return ApiResponse.ok(response);
    }

    @PostMapping
    @Operation(summary = "트라이얼 생성 요청",
            description = "트라이얼을 생성하는 API입니다. Body에 담아 보낼 정보는 난이도 하나만 담아 보내면 됩니다.")
    public ResponseEntity<ApiResponse<TrialInfoResponse>> createTrial(
            @PathVariable("session_id") Long sessionId,
            @RequestBody CreateTrialRequest request,
            @AuthenticationPrincipal CustomUserDetails customUserDetails
    ) {
        TrialInfoResponse response = trialService.createTrial(sessionId, request,
                customUserDetails);

        return ApiResponse.created(response);
    }

    @PutMapping("/{trial_id}")
    @Operation(summary = "트라이얼 수정 요청",
            description = "트라이얼의 정보를 수정하는 API입니다. "
                    + "수정하는 정보로는 난이도가 있습니다.")
    public ResponseEntity<ApiResponse<TrialInfoResponse>> updateTrial(
            @PathVariable("session_id") Long sessionId,
            @PathVariable("trial_id") Long trialId,
            @RequestBody UpdateTrialRequest request,
            @AuthenticationPrincipal CustomUserDetails customUserDetails
    ) {
        TrialInfoResponse response = trialService.updateTrial(sessionId, trialId, request,
                customUserDetails);
        return ApiResponse.ok(response);
    }

    @DeleteMapping("/{trial_id}")
    @Operation(summary = "트라이얼 삭제 요청",
            description = "트라이얼을 삭제하는 API입니다. 연관된 영상과 데이터도 삭제됩니다.ㄴ")
    public ResponseEntity<ApiResponse<Void>> deleteTrial(
            @PathVariable("session_id") Long sessionId,
            @PathVariable("trial_id") Long trialId,
            @AuthenticationPrincipal CustomUserDetails customUserDetails
    ) {
        trialService.deleteTrial(sessionId, trialId, customUserDetails);
        return ApiResponse.ok();
    }
}
