package com.ssafy.a203.domain.video._pose.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.List;

public record JobCreationRequest(
        @JsonProperty("video_url")
        String videoUrl,
        List<HoldInfoDTO> holds
) {

}
