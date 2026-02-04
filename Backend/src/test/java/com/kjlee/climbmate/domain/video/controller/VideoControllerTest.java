package com.kjlee.climbmate.domain.video.controller;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.kjlee.climbmate.common.BaseIntegrationTest;
import com.kjlee.climbmate.domain.exerciseSession.dto.request.CreateSessionRequest;
import com.kjlee.climbmate.domain.exerciseSession.entity.ExerciseSession;
import com.kjlee.climbmate.domain.exerciseSession.service.ExerciseSessionStore;
import com.kjlee.climbmate.domain.trial.dto.request.CreateTrialRequest;
import com.kjlee.climbmate.domain.trial.entity.Trial;
import com.kjlee.climbmate.domain.trial.service.TrialStore;
import com.kjlee.climbmate.domain.user.entity.User;
import com.kjlee.climbmate.domain.user.exception.UserNotFoundException;
import com.kjlee.climbmate.domain.user.repository.UserRepository;
import com.kjlee.climbmate.domain.video.dto.request.SaveVideoRequest;
import com.kjlee.climbmate.domain.video.dto.response.PresignedUrlResponse;
import com.kjlee.climbmate.domain.video.entity.Video;
import com.kjlee.climbmate.domain.video.repository.VideoRepository;
import com.kjlee.climbmate.global.common.util.S3Service;
import com.kjlee.climbmate.global.security.util.JwtProvider;
import java.time.LocalDateTime;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;


public class VideoControllerTest extends BaseIntegrationTest {

    @MockBean
    private S3Service s3Service;

    @Autowired
    private JwtProvider jwtProvider;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private VideoRepository videoRepository;

    @Autowired
    private ExerciseSessionStore sessionStore;

    @Autowired
    private TrialStore trialStore;

    private String token;

    @BeforeEach
    void setLogedIn() throws Exception {
        token = authHelper.signUpAndLogin();
    }

    @Test
    @DisplayName("presigned url 발급 성공")
    void upload_presigned_url_test() throws Exception {
        PresignedUrlResponse mockResponse = new PresignedUrlResponse(
                "uploads/test_123.mp4",
                "https://mock-s3.com/upload"
        );

        when(s3Service.generateUploadUrl("test.mp4")).thenReturn(mockResponse);

        mockMvc.perform(get("/api/v1/videos/pre-signed")
                        .header("Authorization", "Bearer " + token)
                        .param("fileName", "test.mp4"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.fileKey").value("uploads/test_123.mp4"))
                .andExpect(jsonPath("$.data.presignedUrl").value("https://mock-s3.com/upload"));
    }

    @Test
    @DisplayName("영상 정보 저장 성공")
    void save_video_data_success() throws Exception {
        User user = userRepository.findByEmailAndDeletedAtIsNull(jwtProvider.getEmail(token))
                .orElseThrow(UserNotFoundException::new);
        CreateSessionRequest sessionRequest = new CreateSessionRequest("testLocation",
                LocalDateTime.now());
        ExerciseSession session = ExerciseSession.from(sessionRequest, user);
        CreateTrialRequest trialRequest = new CreateTrialRequest("idunno");
        Trial trial = Trial.from(trialRequest, session, user);
        sessionStore.save(session);
        trialStore.save(trial);

        SaveVideoRequest mockReq = new SaveVideoRequest(session.getId(), trial.getId(),
                "testLocation",
                "uploads/test_123.mp4",
                "uploads/test_123.jpg", LocalDateTime.now(), LocalDateTime.now().plusMinutes(10),
                false);

        mockMvc.perform(post("/api/v1/videos")
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(mockReq)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value("SUCCESS"));
    }

    @Test
    @DisplayName("영상 정보 상세 조회 성공")
    void get_video_data_success() throws Exception {
        User curUser = userRepository.findByEmailAndDeletedAtIsNull(jwtProvider.getEmail(token))
                .orElseThrow(
                        UserNotFoundException::new);
        CreateSessionRequest sessionRequest = new CreateSessionRequest("testLocation",
                LocalDateTime.now());
        ExerciseSession session = ExerciseSession.from(sessionRequest, curUser);
        CreateTrialRequest trialRequest = new CreateTrialRequest("idunno");
        Trial trial = Trial.from(trialRequest, session, curUser);
        sessionStore.save(session);
        trialStore.save(trial);
        Video newVideo = videoRepository.save(
                Video.of("uploads/test_123.mp4", "uploads/test_123.jpg", curUser, session, trial));

        mockMvc.perform(get("/api/v1/videos/{video_id}", newVideo.getId())
                        .header("Authorization", "Bearer " + token)
                        .contentType(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.id").value(newVideo.getId()))
                .andExpect(jsonPath("$.data.videoUrl").value(
                        s3Service.generateDownloadUrl(newVideo.getVFileKey())))
                .andExpect(jsonPath("$.data.isAnalyzed").value(false));
    }


}
