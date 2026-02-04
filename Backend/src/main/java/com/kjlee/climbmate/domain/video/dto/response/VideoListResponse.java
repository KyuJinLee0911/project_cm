package com.kjlee.climbmate.domain.video.dto.response;

import java.util.List;

public record VideoListResponse(
        List<VideoInfoResponse> videoInfoList
) {
    public static VideoListResponse from(List<VideoInfoResponse> videoInfoList){
        return new VideoListResponse(videoInfoList);
    }
}
