package com.kjlee.climbmate.domain.video.controller;

import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.csrf;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.JsonNode;
import com.kjlee.climbmate.common.BaseIntegrationTest;
import com.kjlee.climbmate.domain.exerciseSession.dto.request.CreateSessionRequest;
import com.kjlee.climbmate.domain.exerciseSession.entity.ExerciseSession;
import com.kjlee.climbmate.domain.exerciseSession.service.ExerciseSessionStore;
import com.kjlee.climbmate.domain.trial.dto.request.CreateTrialRequest;
import com.kjlee.climbmate.domain.trial.entity.Trial;
import com.kjlee.climbmate.domain.trial.service.TrialStore;
import com.kjlee.climbmate.domain.user.entity.User;
import com.kjlee.climbmate.domain.user.service.UserReader;
import com.kjlee.climbmate.domain.video._hold.dto.request.HoldDetectionRequest;
import com.kjlee.climbmate.domain.video._hold.entity.enums.HoldType;
import com.kjlee.climbmate.domain.video.entity.Video;
import com.kjlee.climbmate.domain.video.repository.VideoRepository;
import com.kjlee.climbmate.global.security.util.JwtProvider;
import java.io.IOException;
import java.net.InetAddress;
import java.time.LocalDateTime;
import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.mock.web.MockMultipartFile;

public class HoldDetectionControllerTest extends BaseIntegrationTest {

    static MockWebServer mockWebServer;

    @Autowired
    VideoRepository videoRepository;

    @Autowired
    UserReader userReader;

    @Autowired
    private ExerciseSessionStore sessionStore;

    @Autowired
    private TrialStore trialStore;

    @Autowired
    JwtProvider jwtProvider;

    private String token;
    private Video video;

    @BeforeAll
    static void setUp() throws IOException {
        mockWebServer = new MockWebServer();
        mockWebServer.start(InetAddress.getByName("127.0.0.1"), 8089);
        String baseUrl = mockWebServer.url("/").toString();

        System.setProperty("ai.base-url", baseUrl);
        System.out.println("MockWebServer started on " + baseUrl);
    }

    @BeforeEach
    void setLogedIn() throws Exception {
        token = authHelper.signUpAndLogin();
        User user = userReader.getUserByEmail(jwtProvider.getEmail(token));
        CreateSessionRequest sessionRequest = new CreateSessionRequest("testLocation",
                LocalDateTime.now());
        ExerciseSession session = ExerciseSession.from(sessionRequest, user);
        CreateTrialRequest trialRequest = new CreateTrialRequest("idunno");
        Trial trial = Trial.from(trialRequest, session, user);
        sessionStore.save(session);
        trialStore.save(trial);
        video = Video.of("testFile", "testFile2", user, session, trial);
        videoRepository.save(video);
    }

    @AfterAll
    static void tearDown() throws IOException {
        mockWebServer.shutdown();
    }

    @Test
    void holdDetectionTest() throws Exception {
        // 세션 열기
        mockWebServer.enqueue(new MockResponse()
                .setBody("{\"session_id\":\"testSession\"}")
                .addHeader("Content-Type", "application/json")
                .setResponseCode(201));

        MockMultipartFile file = new MockMultipartFile(
                "file",
                "test.jpg",
                "image/jpg",
                "dummy data".getBytes()
        );

        mockMvc.perform(multipart("/api/v1/videos/{video_id}/holds/detect/open", video.getId())
                        .file(file)
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.MULTIPART_FORM_DATA)
                        .with(csrf()))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.data.sessionId").value("testSession"));

        // 열린 세션 상태 응답
        mockWebServer.enqueue(new MockResponse()
                .setBody("{\"session_id\":\"testSession\",\"status\":\"active\"}")
                .addHeader("Content-Type", "application/json")
                .setResponseCode(200));

        // 홀드 인식 응답 -> 이 응답은 ai 서버를 mocking한 서버가 하는 응답이지 백엔드 서버의 응답이 아님. 헷갈리지 말것
        mockWebServer.enqueue(new MockResponse()
                .setBody("""
                        {
                          "points": [[158,322],[158,323],[158,324],[157,325],[157,327]]
                        }
                        """)
                .addHeader("Content-Type", "application/json")
                .setResponseCode(200));

        // 세션 종료 응답
        mockWebServer.enqueue(new MockResponse()
                .setBody("""
                        {
                            "ok":true
                        }
                        """)
                .addHeader("Content-Type", "application/json")
                .setResponseCode(200));

        HoldDetectionRequest request = new HoldDetectionRequest(120.0, 200.0, HoldType.START);

        var result = mockMvc.perform(post("/api/v1/videos/{video_id}/holds/detect", video.getId())
                        .param("last", "true")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.holdId").value(1L))
                .andExpect(jsonPath("$.data.x").value(120.0))
                .andExpect(jsonPath("$.data.y").value(200.0))
                .andReturn();
        String json = result.getResponse().getContentAsString();
        JsonNode root = objectMapper.readTree(json);

        Long holdId = root.path("data").get("holdId").asLong();

        var recordedRequest = mockWebServer.takeRequest();
        System.out.println(recordedRequest.getPath());
        System.out.println(recordedRequest.getBody().readUtf8());

        mockMvc.perform(
                        delete("/api/v1/videos/{video_id}/holds/detect/{hold_id}", video.getId(), holdId)
                                .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk());

    }
}
