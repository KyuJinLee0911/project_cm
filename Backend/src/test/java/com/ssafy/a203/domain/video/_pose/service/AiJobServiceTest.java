package com.ssafy.a203.domain.video._pose.service;


import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

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
import com.ssafy.a203.domain.video.entity.Video;
import com.ssafy.a203.domain.video.service.VideoStore;
import com.ssafy.a203.global.security.util.JwtProvider;
import java.io.IOException;
import java.net.InetAddress;
import java.time.LocalDateTime;
import java.util.List;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.data.redis.listener.RedisMessageListenerContainer;
import org.springframework.http.MediaType;

@ExtendWith(MockitoExtension.class)
public class AiJobServiceTest extends BaseIntegrationTest {

    @MockBean
    private RedisMessageListenerContainer redisContainer;

    static MockWebServer mockWebServer;

    @Autowired
    UserReader userReader;

    @Autowired
    JwtProvider jwtProvider;

    @Autowired
    private VideoStore videoStore;

    @Autowired
    private ExerciseSessionStore sessionStore;

    @Autowired
    private TrialStore trialStore;

    private String token;

    @BeforeAll
    static void setupServer() throws Exception {
        mockWebServer = new MockWebServer();
        mockWebServer.start(InetAddress.getByName("127.0.0.1"), 8089);
        String baseUrl = mockWebServer.url("/").toString();

        System.setProperty("ai.base-url", baseUrl);
        System.out.println("MockWebServer started on " + baseUrl);
    }

    @BeforeEach
    void setup() throws Exception {
        token = authHelper.signUpAndLogin();
    }

    @AfterAll
    static void tearDown() throws IOException {
        mockWebServer.shutdown();
    }

    @Test
    void shouldSendCorrectPayloadToAiServer() throws Exception {
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

        mockWebServer.enqueue(new MockResponse()
                .setBody("{\"job_id\":\"job-123\",\"message\":\"queued\"}")
                .addHeader("Content-Type", "application/json")
                .setResponseCode(201));

        mockMvc.perform(post("/api/v1/videos/{video_id}/analysis", video.getId())
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.data.job_id").value("job-123"))
                .andExpect(jsonPath("$.data.status").value("queued"));

        var recordedRequest = mockWebServer.takeRequest();
        System.out.println(recordedRequest.getPath());
        System.out.println(recordedRequest.getBody().readUtf8());
    }
}
