package com.ssafy.a203.domain.exerciseSession.controller;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.jayway.jsonpath.JsonPath;
import com.ssafy.a203.common.BaseIntegrationTest;
import com.ssafy.a203.domain.exerciseSession.dto.request.CreateSessionRequest;
import com.ssafy.a203.domain.exerciseSession.dto.response.SessionDetailResponse;
import com.ssafy.a203.domain.exerciseSession.dto.response.SessionListResponse;
import com.ssafy.a203.domain.exerciseSession.entity.ExerciseSession;
import com.ssafy.a203.domain.exerciseSession.service.ExerciseSessionStore;
import com.ssafy.a203.domain.trial.dto.request.CreateTrialRequest;
import com.ssafy.a203.domain.trial.entity.Trial;
import com.ssafy.a203.domain.trial.service.TrialStore;
import com.ssafy.a203.domain.user.entity.User;
import com.ssafy.a203.domain.user.service.UserReader;
import com.ssafy.a203.global.security.util.JwtProvider;
import java.time.LocalDateTime;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MvcResult;

public class ExerciseSessionControllerTest extends BaseIntegrationTest {

    @Autowired
    private ExerciseSessionStore sessionStore;

    @Autowired
    private JwtProvider jwtProvider;

    @Autowired
    private UserReader userReader;

    @Autowired
    private TrialStore trialStore;

    private String token;
    private ExerciseSession session;
    private User user;

    @BeforeEach
    void setup() throws Exception {
        token = this.authHelper.signUpAndLogin();
        CreateSessionRequest csReqeust = new CreateSessionRequest("testLocation",
                LocalDateTime.now());
        user = userReader.getUserByEmail(jwtProvider.getEmail(token));
        session = ExerciseSession.from(csReqeust, user);
        sessionStore.save(session);
    }

    @Test
    @DisplayName("세션 생성 성공")
    void shouldCreateSession_whenRequestIsValid() throws Exception {
        LocalDateTime time = LocalDateTime.now();
        CreateSessionRequest request = new CreateSessionRequest("testLocation",
                time);

        MvcResult result = mockMvc.perform(post("/api/v1/sessions")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andReturn();

        String location = JsonPath.read(result.getResponse().getContentAsString(),
                "$.data.location");
        String startedAt = JsonPath.read(result.getResponse().getContentAsString(),
                "$.data.startedAt");

        LocalDateTime actualTime = LocalDateTime.parse(startedAt);

        assertThat(actualTime).isEqualTo(time);
        assertThat(location).isEqualTo(request.location());
    }

    @Test
    @DisplayName("세션 목록 조회 성공")
    void shouldGetSessionList_whenRequestIsValid() throws Exception {
        MvcResult result = mockMvc.perform(get("/api/v1/sessions")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andReturn();
        Object data = JsonPath.read(result.getResponse().getContentAsString(), "$.data");
        SessionListResponse list = objectMapper.convertValue(data, SessionListResponse.class);
        boolean exists = list.sessions().stream()
                .anyMatch(s -> s.sessionId().equals(session.getId()));

        assertThat(exists).isTrue();
    }

    @Test
    @DisplayName("세션 상세 조회 성공")
    void shouldGetSessionDetail_whenRequestIsValid() throws Exception {
        CreateTrialRequest ctRequest = new CreateTrialRequest("orange");
        Trial trial = Trial.from(ctRequest, session, user);
        trialStore.save(trial);

        MvcResult result = mockMvc.perform(get("/api//v1/sessions/{session_id}", session.getId())
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andReturn();

        Object response = JsonPath.read(result.getResponse().getContentAsString(), "$.data");
        SessionDetailResponse detail = objectMapper.convertValue(response,
                SessionDetailResponse.class);

        boolean exists = detail.trials().stream()
                .anyMatch(t -> t.trialId().equals(trial.getId()));

        assertThat(detail.sessionId().equals(session.getId()));
        assertThat(exists).isTrue();
    }

    @Test
    @DisplayName("세션 수정 성공")
    void shouldUpdateSession_whenRequestIsValid() throws Exception {
        mockMvc.perform(put("/api/v1/sessions/{session_id}", session.getId())
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.endedAt").exists())
                .andExpect(jsonPath("$.data.duration").exists());
    }

    @Test
    @DisplayName("세션 삭제 성공")
    void shouldDeleteSession_whenRequestIsValid() throws Exception {
        mockMvc.perform(delete("/api/v1/sessions/{session_id}", session.getId())
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk());
    }
}
