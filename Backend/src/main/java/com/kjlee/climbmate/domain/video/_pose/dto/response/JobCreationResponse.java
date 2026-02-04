package com.kjlee.climbmate.domain.video._pose.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;

public record JobCreationResponse(
        @JsonProperty("job_id") String jobId,
        String message
) {

}
