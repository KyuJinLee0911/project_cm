package com.ssafy.a203.domain.video.controller;

import com.ssafy.a203.domain.video.dto.request.SaveVideoRequest;
import com.ssafy.a203.domain.video.dto.response.PresignedUrlResponse;
import com.ssafy.a203.domain.video.dto.response.VideoDetailResponse;
import com.ssafy.a203.domain.video.dto.response.VideoListResponse;
import com.ssafy.a203.domain.video.service.VideoService;
import com.ssafy.a203.global.common.dto.ApiResponse;
import com.ssafy.a203.global.common.util.S3Service;
import com.ssafy.a203.global.security.dto.CustomUserDetails;
import io.swagger.v3.oas.annotations.Operation;
import jakarta.validation.Valid;
import java.time.LocalDate;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/videos")
public class VideoController {

    private final VideoService videoService;
    private final S3Service s3Service;

    @GetMapping("/pre-signed")
    @Operation(summary = "업로드 URL 요청",
            description = "프론트엔드에서 영상 업로드를 위해 필요한 PresignedUrl을 요청하는 API 입니다. <br>"
                    + "Presigned Url과 fileKey를 응답으로 반환합니다.")
    public ResponseEntity<ApiResponse<PresignedUrlResponse>> getUploadPresigned(
            @RequestParam String fileName) {
        PresignedUrlResponse res = s3Service.generateUploadUrl(fileName);
        return ApiResponse.ok(res);
    }

    @PostMapping
    @Operation(summary = "영상 정보 등록",
            description = "영상을 S3에 저장하고 나서 해당 영상의 정보를 DB에 저장하기 위한 API 입니다. <br>"
                    + "PresignedUrl 요청 시 응답으로 받았던 fileKey와 운동 장소를 보내면 이 내용을 조합해 DB에 저장합니다.")
    public ResponseEntity<ApiResponse<VideoDetailResponse>> saveVideo(
            @RequestBody @Valid SaveVideoRequest saveRequest,
            @AuthenticationPrincipal CustomUserDetails customUserDetails
    ) {
        videoService.saveVideoAndExerciseInfo(saveRequest,
                customUserDetails);
        return ApiResponse.ok();
    }

    @GetMapping("/{video_id}")
    @Operation(summary = "영상 상세 정보 조회",
            description = "목록에서 video_id를 활용해 영상 시청을 위한 상세 조회 API 입니다. <br>"
                    + "id를 통해 영상의 정보를 찾아 영상 다운로드용 presigned url을 포함한 영상의 정보를 반환합니다.")
    public ResponseEntity<ApiResponse<VideoDetailResponse>> getVideoDetail(
            @PathVariable("video_id") Long videoId,
            @AuthenticationPrincipal CustomUserDetails customUserDetails
    ) {
        VideoDetailResponse videoDetailResponse = videoService.getVideoDetail(videoId,
                customUserDetails);
        return ApiResponse.ok(videoDetailResponse);
    }

    @GetMapping("")
    @Operation(summary = "조건부 영상 목록 조회",
            description = "영상 리스트를 조회하는 API 입니다. <br>"
                    + "조회를 원하는 날짜(ex. 2025-11-05)를 request parameter에 넣으면 해당 날짜의 영상 목록을 반환합니다. "
                    + "날짜를 넣지 않으면 해당하는 유저의 전체 영상 목록을 반환합니다.")
    public ResponseEntity<ApiResponse<VideoListResponse>> getVideoListByCondition(
            @RequestParam(required = false) LocalDate date,
            @AuthenticationPrincipal CustomUserDetails customUserDetails
    ) {
        VideoListResponse response;
        if (date != null) {
            response = videoService.getVideoListByDate(date, customUserDetails);
        } else {
            response = videoService.getVideoList(customUserDetails);
        }

        return ApiResponse.ok(response);
    }
}