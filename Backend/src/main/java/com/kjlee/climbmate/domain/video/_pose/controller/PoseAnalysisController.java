package com.kjlee.climbmate.domain.video._pose.controller;

import com.kjlee.climbmate.domain.video._pose.dto.request.JobCreationRequest;
import com.kjlee.climbmate.domain.video._pose.dto.response.AiJobResponse;
import com.kjlee.climbmate.domain.video._pose.service.AiJobService;
import com.kjlee.climbmate.global.common.dto.ApiResponse;
import com.kjlee.climbmate.global.security.dto.CustomUserDetails;
import io.swagger.v3.oas.annotations.Operation;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/videos/{video_id}/analysis")
public class PoseAnalysisController {

    private final AiJobService aiJobService;

    @PostMapping
    @Operation(summary = "자세 분석 요청",
            description =
                    "자세 분석을 요청합니다. ai 서버에 비동기 분석 요청을 보내고, 분석 job을 queue에 넣습니다. job id를 리턴받습니다. "
                            + "리턴받은 job id를 통해 web socket 요청을 보내 redis subscribe를 하면 "
                            + "분석 완료 시 ai 서버에서 자동으로 분석 결과를 publish 합니다.")
    public ResponseEntity<ApiResponse<AiJobResponse>> createAiJob(
            @PathVariable("video_id") Long videoId,
            @RequestBody JobCreationRequest request,
            @AuthenticationPrincipal CustomUserDetails customUserDetails
    ) {
        AiJobResponse response = aiJobService.createJob(videoId, request);
        return ApiResponse.created(response);
    }

    @GetMapping
    @Operation(summary = "저장된 분석 정보 불러오기",
            description = "db에 저장된 자세 분석 정보를 불러옵니다. 분석 정보가 없을 경우 exception을 throw 합니다.")
    public ResponseEntity<ApiResponse<AiJobResponse>> getAnalyzedData(
            @PathVariable("video_id") Long videoId,
            @AuthenticationPrincipal CustomUserDetails customUserDetails
    ) {
        AiJobResponse response = aiJobService.getAnalyzedData(videoId, customUserDetails);
        return ApiResponse.ok(response);
    }
}

