package com.ssafy.a203.domain.video._hold.dto.response;

import java.util.List;

public record HoldListResponse(
        Long videoId,
        List<HoldInfoResponse> holdInfos
) {

    public static HoldListResponse of(Long videoId, List<HoldInfoResponse> holdInfos) {
        return new HoldListResponse(videoId, holdInfos);
    }
}
