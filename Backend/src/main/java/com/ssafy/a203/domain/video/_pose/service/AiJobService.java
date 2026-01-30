package com.ssafy.a203.domain.video._pose.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.a203.domain.user.exception.UnauthorizedUserException;
import com.ssafy.a203.domain.video._pose.dto.request.JobCreationRequest;
import com.ssafy.a203.domain.video._pose.dto.response.AiJobResponse;
import com.ssafy.a203.domain.video._pose.dto.response.JobCreationResponse;
import com.ssafy.a203.domain.video._pose.entity.AnalyzedData;
import com.ssafy.a203.domain.video._pose.exception.DataNotFoundException;
import com.ssafy.a203.domain.video.entity.Video;
import com.ssafy.a203.domain.video.service.VideoReader;
import com.ssafy.a203.global.security.dto.CustomUserDetails;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestClient;

@Slf4j
@Service
@RequiredArgsConstructor
public class AiJobService {

    private final SimpMessagingTemplate messagingTemplate;
    private final ObjectMapper objectMapper;
    private final RestClient restClient;
    private final VideoReader videoReader;
    private final JobReader jobReader;
    private final JobStore jobStore;

    @Transactional
    public void handleJobResult(AiJobResponse result) {
        try {
            AnalyzedData data = jobReader.getById(result.jobId());
            data.updateStatus(result.status(), result.message());
            data.updateResult(objectMapper.writeValueAsString(result.result()));

            jobStore.save(data);
            data.getVideo().markAsAnalyzed();

            messagingTemplate.convertAndSend(
                    "/topic/ai/jobs/" + result.jobId(),
                    result
            );
        } catch (Exception e) {
            log.error("Failded to handle AI Job result : {}", e.getMessage(), e);
        }
    }

    public AiJobResponse createJob(Long videoId, JobCreationRequest request) {
        Video video = videoReader.getByVideoId(videoId);
        JobCreationResponse result = restClient.post()
                .uri("/ai/v1/analysis/jobs")
                .contentType(MediaType.APPLICATION_JSON)
                .body(request)
                .retrieve()
                .body(JobCreationResponse.class);

        AnalyzedData data = AnalyzedData.of(
                result.jobId(),
                result.message(),
                null,
                null,
                video
        );

        log.info(data.getId());
        log.info(data.getStatus());

        return AiJobResponse.from(jobStore.save(data));
    }

    public AiJobResponse getAnalyzedData(Long videoId, CustomUserDetails customUserDetails) {
        Video video = videoReader.getByVideoId(videoId);
        if (!video.getUser().getId().equals(customUserDetails.id())) {
            throw new UnauthorizedUserException();
        }

        if (!video.isAnalyzed()) {
            throw new DataNotFoundException();
        }

        AnalyzedData data = jobReader.getByVideoId(videoId);
        return AiJobResponse.from(data);
    }
}
