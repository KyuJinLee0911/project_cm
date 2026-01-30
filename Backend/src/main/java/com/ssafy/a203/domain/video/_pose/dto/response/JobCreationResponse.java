package com.ssafy.a203.domain.video._pose.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;

public record JobCreationResponse(
        @JsonProperty("job_id") String jobId,
        String message
) {

}
