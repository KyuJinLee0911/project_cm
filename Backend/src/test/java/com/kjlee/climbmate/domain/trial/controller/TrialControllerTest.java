package com.kjlee.climbmate.domain.trial.controller;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.jayway.jsonpath.JsonPath;
import com.kjlee.climbmate.common.BaseIntegrationTest;
import com.kjlee.climbmate.domain.exerciseInfo.entity.ExerciseInfo;
import com.kjlee.climbmate.domain.exerciseInfo.service.ExerciseInfoStore;
import com.kjlee.climbmate.domain.exerciseSession.dto.request.CreateSessionRequest;
import com.kjlee.climbmate.domain.exerciseSession.entity.ExerciseSession;
import com.kjlee.climbmate.domain.exerciseSession.service.ExerciseSessionStore;
import com.kjlee.climbmate.domain.trial.dto.request.CreateTrialRequest;
import com.kjlee.climbmate.domain.trial.dto.request.UpdateTrialRequest;
import com.kjlee.climbmate.domain.trial.dto.response.TrialDetailResponse;
import com.kjlee.climbmate.domain.trial.entity.Trial;
import com.kjlee.climbmate.domain.trial.service.TrialStore;
import com.kjlee.climbmate.domain.user.entity.User;
import com.kjlee.climbmate.domain.user.service.UserReader;
import com.kjlee.climbmate.domain.video.entity.Video;
import com.kjlee.climbmate.domain.video.service.VideoStore;
import com.kjlee.climbmate.global.security.util.JwtProvider;
import java.time.LocalDateTime;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MvcResult;

public class TrialControllerTest extends BaseIntegrationTest {

    @Autowired
    private ExerciseSessionStore sessionStore;

    @Autowired
    private JwtProvider jwtProvider;

    @Autowired
    private UserReader userReader;

    @Autowired
    private TrialStore trialStore;

    @Autowired
    private VideoStore videoStore;

    @Autowired
    private ExerciseInfoStore infoStore;

    private String token;
    private ExerciseSession session;
    private User user;
    private Trial trial;

    @BeforeEach
    void setup() throws Exception {
        token = this.authHelper.signUpAndLogin();
        CreateSessionRequest csReqeust = new CreateSessionRequest("testLocation",
                LocalDateTime.now());
        user = userReader.getUserByEmail(jwtProvider.getEmail(token));

        session = ExerciseSession.from(csReqeust, user);
        sessionStore.save(session);

        CreateTrialRequest createTrialRequest = new CreateTrialRequest("orange");
        trial = Trial.from(createTrialRequest, session, user);
        trialStore.save(trial);
    }

    @Test
    @DisplayName("트라이얼 생성 성공")
    void shouldCreateTrial_whenRequestIsValid() throws Exception {
        CreateTrialRequest createTrialRequest = new CreateTrialRequest("blue");

        mockMvc.perform(post("/api/v1/sessions/{session_id}/trials", session.getId())
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(createTrialRequest)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.data.difficulty").value("blue"));
    }

    @Test
    @DisplayName("트라이얼 조회 성공")
    void shouldGetTrialDetail_whenRequestIsValid() throws Exception {
        Video video = Video.of("testKey", "testKey2", user, session, trial);
        videoStore.save(video);

        LocalDateTime now = LocalDateTime.now();
        ExerciseInfo info = ExerciseInfo.of(now, now.plusMinutes(10), true, video);
        infoStore.save(info);

        MvcResult result = mockMvc.perform(
                        get("/api/v1/sessions/{session_id}/trials/{trial_id}", session.getId(),
                                trial.getId())
                                .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andReturn();

        Object response = JsonPath.read(result.getResponse().getContentAsString(), "$.data");
        TrialDetailResponse detail = objectMapper.convertValue(response, TrialDetailResponse.class);
        boolean exists = detail.videoSummaries().stream()
                .anyMatch(tdr -> tdr.videoId().equals(video.getId()));

        assertThat(exists).isTrue();
        assertThat(detail.trialId()).isEqualTo(trial.getId());
    }

    @Test
    @DisplayName("트라이얼 수정 성공")
    void shouldUpdateTrial_whenRequestIsValid() throws Exception {
        UpdateTrialRequest updateTrialRequest = new UpdateTrialRequest("black");

        mockMvc.perform(put("/api/v1/sessions/{session_id}/trials/{trial_id}", session.getId(),
                        trial.getId())
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(updateTrialRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.difficulty").value("black"));
    }

    @Test
    @DisplayName("트라이얼 삭제 성공")
    void shouldDeleteTrial_whenRequestIsValid() throws Exception {
        mockMvc.perform(delete("/api/v1/sessions/{session_id}/trials/{trial_id}", session.getId(),
                        trial.getId())
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk());
    }

}
