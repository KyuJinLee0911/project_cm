package com.ssafy.a203.domain.video.controller;

import static org.hamcrest.Matchers.startsWith;
import static org.hamcrest.collection.IsCollectionWithSize.hasSize;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
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
import com.ssafy.a203.domain.user.exception.UserNotFoundException;
import com.ssafy.a203.domain.user.repository.UserRepository;
import com.ssafy.a203.domain.video.entity.Video;
import com.ssafy.a203.domain.video.repository.VideoRepository;
import com.ssafy.a203.global.security.util.JwtProvider;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.TimeZone;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

public class VideoControllerListTest extends BaseIntegrationTest {

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
    void setup() throws Exception {
        TimeZone.setDefault(TimeZone.getTimeZone("Asia/Seoul"));
        token = this.authHelper.signUpAndLogin();
        LocalDateTime fixedDate = LocalDate.of(2025, 11, 17).atStartOfDay();

        User curUser = userRepository.findByEmailAndDeletedAtIsNull(jwtProvider.getEmail(token))
                .orElseThrow(
                        UserNotFoundException::new);
        CreateSessionRequest sessionRequest = new CreateSessionRequest("testLocation",
                fixedDate);
        ExerciseSession session = ExerciseSession.from(sessionRequest, curUser);
        CreateTrialRequest trialRequest = new CreateTrialRequest("idunno");
        Trial trial = Trial.from(trialRequest, session, curUser);
        sessionStore.save(session);
        trialStore.save(trial);

        Video newVideo = Video.of("uploads/test_123.mp4", "uploads/test_123.jpg",
                curUser, session, trial);
        newVideo.setCreatedAt(fixedDate.plusDays(2));
        videoRepository.save(newVideo);

        Video newVideo2 = Video.of("uploads/test_124.mp4", "uploads/test_124.jpg",
                curUser, session, trial);
        newVideo2.setCreatedAt(fixedDate.plusDays(2));
        videoRepository.save(newVideo2);

        Video newVideo3 = videoRepository.save(
                Video.of("uploads/test_125.mp4", "uploads/test_125.jpg", curUser, session, trial));
        newVideo3.setCreatedAt(fixedDate);
        videoRepository.save(newVideo3);

        Video newVideo4 = videoRepository.save(
                Video.of("uploads/test_126.mp4", "uploads/test_126.jpg", curUser, session, trial));
        newVideo4.setCreatedAt(fixedDate);
        videoRepository.save(newVideo4);
    }

    @Test
    @DisplayName("영상 목록 조회 성공")
    void get_video_list_success() throws Exception {
        mockMvc.perform(get("/api/v1/videos")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.videoInfoList", hasSize(4)));
    }

    @Test
    @DisplayName("특정 일자 영상 목록 조회 성공")
    void get_video_list_by_date_success() throws Exception {
        LocalDate fixedDate = LocalDate.of(2025, 11, 17);
        String today = String.valueOf(fixedDate);
        var res = mockMvc.perform(get("/api/v1/videos")
                        .header("Authorization", "Bearer " + token)
                        .param("date", today))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.videoInfoList", hasSize(2)))
                .andExpect(jsonPath("$.data.videoInfoList[0].createdAt", startsWith(today)))
                .andExpect(jsonPath("$.data.videoInfoList[1].createdAt", startsWith(today)));
    }
}
