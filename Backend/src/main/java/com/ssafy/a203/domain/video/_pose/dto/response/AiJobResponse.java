package com.ssafy.a203.domain.video._pose.dto.response;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.ssafy.a203.domain.video._pose.entity.AnalyzedData;

public record AiJobResponse(
        @JsonProperty("job_id")
        String jobId,
        String status,
        String message,
        Object result
) {

    public static AiJobResponse from(AnalyzedData data) {
        return new AiJobResponse(data.getId(), data.getStatus(), data.getMessage(),
                data.getResultJson());
    }
}
