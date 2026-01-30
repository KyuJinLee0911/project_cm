package com.ssafy.a203.domain.video._pose.controller;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.ssafy.a203.common.BaseIntegrationTest;
import com.ssafy.a203.domain.exerciseSession.dto.request.CreateSessionRequest;
import com.ssafy.a203.domain.exerciseSession.entity.ExerciseSession;
import com.ssafy.a203.domain.exerciseSession.service.ExerciseSessionStore;
import com.ssafy.a203.domain.trial.dto.request.CreateTrialRequest;
import com.ssafy.a203.domain.trial.entity.Trial;
import com.ssafy.a203.domain.trial.service.TrialStore;
import com.ssafy.a203.domain.user.entity.User;
import com.ssafy.a203.domain.user.service.UserReader;
import com.ssafy.a203.domain.video._hold.entity.enums.HoldType;
import com.ssafy.a203.domain.video._pose.dto.request.HoldInfoDTO;
import com.ssafy.a203.domain.video._pose.dto.request.JobCreationRequest;
import com.ssafy.a203.domain.video._pose.dto.response.AiJobResponse;
import com.ssafy.a203.domain.video._pose.service.AiJobService;
import com.ssafy.a203.domain.video.entity.Video;
import com.ssafy.a203.domain.video.service.VideoStore;
import com.ssafy.a203.global.security.util.JwtProvider;
import java.time.LocalDateTime;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.data.redis.listener.RedisMessageListenerContainer;
import org.springframework.http.MediaType;

public class PoseAnalysisControllerTest extends BaseIntegrationTest {

    @MockBean
    private AiJobService aiJobService;

    @Autowired
    private UserReader userReader;

    @Autowired
    private JwtProvider jwtProvider;

    @MockBean
    private RedisMessageListenerContainer redisContainer;

    @Autowired
    private VideoStore videoStore;

    @Autowired
    private ExerciseSessionStore sessionStore;

    @Autowired
    private TrialStore trialStore;

    private String token;

    @BeforeEach
    void setUp() throws Exception {
        token = authHelper.signUpAndLogin();

        objectMapper.setPropertyNamingStrategy(PropertyNamingStrategies.SNAKE_CASE);
    }

    @Test
    void createAnalysisJob() throws Exception {
        HoldInfoDTO infoDto = new HoldInfoDTO(HoldType.START, List.of(
                List.of(10.0, 20.0),
                List.of(10.0, 20.0)
        ), List.of(10.0, 20.0));
        HoldInfoDTO infoDto2 = new HoldInfoDTO(HoldType.TOP, List.of(
                List.of(11.0, 21.0),
                List.of(12.0, 22.0)
        ), List.of(10.0, 20.0));
        JobCreationRequest request = new JobCreationRequest("https://testUrl/", List.of(
                infoDto,
                infoDto2
        ));
        User user = userReader.getUserByEmail(jwtProvider.getEmail(token));
        CreateSessionRequest sessionRequest = new CreateSessionRequest("testLocation",
                LocalDateTime.now());
        ExerciseSession session = ExerciseSession.from(sessionRequest, user);
        CreateTrialRequest trialRequest = new CreateTrialRequest("idunno");
        Trial trial = Trial.from(trialRequest, session, user);
        sessionStore.save(session);
        trialStore.save(trial);
        Video video = videoStore.save(Video.of("testKey", "testKey2", user, session, trial));

        AiJobResponse response = new AiJobResponse("job-123", "queued", null, null);
        given(aiJobService.createJob(any(), any())).willReturn(response);

        mockMvc.perform(post("/api/v1/videos/{video_id}/analysis", video.getId())
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.data.job_id").value("job-123"))
                .andExpect(jsonPath("$.data.status").value("queued"));
    }
}
