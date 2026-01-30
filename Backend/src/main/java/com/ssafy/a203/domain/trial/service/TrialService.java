package com.ssafy.a203.domain.trial.service;

import com.ssafy.a203.domain.exerciseSession.entity.ExerciseSession;
import com.ssafy.a203.domain.exerciseSession.service.ExerciseSessionDeleteService;
import com.ssafy.a203.domain.exerciseSession.service.ExerciseSessionReader;
import com.ssafy.a203.domain.trial.dto.request.CreateTrialRequest;
import com.ssafy.a203.domain.trial.dto.request.UpdateTrialRequest;
import com.ssafy.a203.domain.trial.dto.response.TrialDetailResponse;
import com.ssafy.a203.domain.trial.dto.response.TrialInfoResponse;
import com.ssafy.a203.domain.trial.entity.Trial;
import com.ssafy.a203.domain.trial.exception.TrialAccessDeniedException;
import com.ssafy.a203.domain.user.entity.User;
import com.ssafy.a203.domain.user.exception.UnauthorizedUserException;
import com.ssafy.a203.domain.user.service.UserReader;
import com.ssafy.a203.domain.video.dto.VideoSummaryProjection;
import com.ssafy.a203.domain.video.dto.response.VideoSummary;
import com.ssafy.a203.domain.video.service.VideoReader;
import com.ssafy.a203.global.common.util.S3Service;
import com.ssafy.a203.global.security.dto.CustomUserDetails;
import java.util.List;
import java.util.Objects;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class TrialService {

    private final ExerciseSessionDeleteService delete;
    private final TrialReader trialReader;
    private final TrialStore trialStore;
    private final UserReader userReader;
    private final ExerciseSessionReader sessionReader;
    private final VideoReader videoReader;
    private final S3Service s3Service;

    @Transactional(readOnly = true)
    public TrialDetailResponse getTrialDetail(Long sessionId, Long trialId,
            CustomUserDetails customUserDetails) {
        Trial trial = authCheck(trialId, customUserDetails);
        sessionCheck(trial, sessionId);

        List<VideoSummaryProjection> spList = videoReader.getSummaryByTrialId(trialId);
        List<VideoSummary> videoSummaries = spList.stream()
                .map(videoSummaryProjection -> VideoSummary.of(
                        videoSummaryProjection.videoId(),
                        s3Service.generateDownloadUrl(videoSummaryProjection.thumbnailUrl()),
                        videoSummaryProjection.isAnalyzed(),
                        videoSummaryProjection.succeeded())).toList();
        return TrialDetailResponse.of(trialId, videoSummaries);
    }

    @Transactional
    public TrialInfoResponse createTrial(Long sessionId, CreateTrialRequest request,
            CustomUserDetails customUserDetails) {
        User user = userReader.getUserByEmail(customUserDetails.email());
        ExerciseSession session = sessionReader.getSession(sessionId);
        Trial trial = Trial.from(request, session, user);
        return TrialInfoResponse.from(trialStore.save(trial));
    }

    @Transactional
    public TrialInfoResponse updateTrial(Long sessionId, Long trialId, UpdateTrialRequest request,
            CustomUserDetails customUserDetails) {
        Trial trial = authCheck(trialId, customUserDetails);
        sessionCheck(trial, sessionId);
        trial.updateTrial(request);
        return TrialInfoResponse.from(trial);
    }

    @Transactional
    public void deleteTrial(Long sessionId, Long trialId, CustomUserDetails customUserDetails) {
        Trial trial = authCheck(trialId, customUserDetails);
        sessionCheck(trial, sessionId);
        delete.deleteTrial(trialId);
    }

    private Trial authCheck(Long trialId, CustomUserDetails customUserDetails) {
        Trial trial = trialReader.getById(trialId);
        if (!trial.getUser().getId().equals(customUserDetails.id())) {
            throw new UnauthorizedUserException();
        }
        return trial;
    }

    private void sessionCheck(Trial trial, Long sessionId) {
        if (!Objects.equals(trial.getExerciseSession().getId(), sessionId)) {
            throw new TrialAccessDeniedException();
        }
    }
}
