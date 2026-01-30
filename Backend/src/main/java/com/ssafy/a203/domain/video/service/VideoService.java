package com.ssafy.a203.domain.video.service;

import com.ssafy.a203.domain.exerciseInfo.entity.ExerciseInfo;
import com.ssafy.a203.domain.exerciseInfo.service.ExerciseInfoStore;
import com.ssafy.a203.domain.exerciseSession.entity.ExerciseSession;
import com.ssafy.a203.domain.exerciseSession.service.ExerciseSessionReader;
import com.ssafy.a203.domain.trial.entity.Trial;
import com.ssafy.a203.domain.trial.service.TrialReader;
import com.ssafy.a203.domain.user.entity.User;
import com.ssafy.a203.domain.user.exception.UnauthorizedUserException;
import com.ssafy.a203.domain.user.service.UserReader;
import com.ssafy.a203.domain.video.dto.request.SaveVideoRequest;
import com.ssafy.a203.domain.video.dto.response.VideoDetailResponse;
import com.ssafy.a203.domain.video.dto.response.VideoInfoResponse;
import com.ssafy.a203.domain.video.dto.response.VideoListResponse;
import com.ssafy.a203.domain.video.entity.Video;
import com.ssafy.a203.global.common.util.S3Service;
import com.ssafy.a203.global.security.dto.CustomUserDetails;
import java.time.LocalDate;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class VideoService {

    private final VideoStore videoStore;
    private final VideoReader videoReader;
    private final UserReader userReader;
    private final S3Service s3Service;
    private final ExerciseInfoStore exerciseInfoStore;
    private final ExerciseSessionReader sessionReader;
    private final TrialReader trialReader;

    @Transactional(readOnly = true)
    public VideoListResponse getVideoList(CustomUserDetails customUserDetails) {
        List<VideoInfoResponse> videoList = videoReader.getAllByUserId(customUserDetails.id())
                .stream()
                .map(vi -> VideoInfoResponse.of(
                        vi.videoId(),
                        vi.createdAt(),
                        vi.isAnalyzed(),
                        vi.isSuccesses(),
                        s3Service.generateDownloadUrl(vi.thumbnailKey())
                ))
                .toList();

        return VideoListResponse.from(videoList);
    }

    @Transactional(readOnly = true)
    public VideoListResponse getVideoListByDate(LocalDate date,
            CustomUserDetails customUserDetails) {
        List<VideoInfoResponse> videoList = videoReader.getAllByDate(date, customUserDetails.id())
                .stream()
                .map(vi -> VideoInfoResponse.of(
                        vi.videoId(),
                        vi.createdAt(),
                        vi.isAnalyzed(),
                        vi.isSuccesses(),
                        s3Service.generateDownloadUrl(vi.thumbnailKey())
                ))
                .toList();
        return VideoListResponse.from(videoList);
    }

    @Transactional(readOnly = true)
    public VideoDetailResponse getVideoDetail(Long videoId, CustomUserDetails customUserDetails) {
        Video video = videoReader.getByVideoId(videoId);
        if (!video.getUser().getId().equals(customUserDetails.id())) {
            throw new UnauthorizedUserException();
        }
        String videoUrl = s3Service.generateDownloadUrl(video.getVFileKey());

        return VideoDetailResponse.of(videoId, videoUrl, video.isAnalyzed());
    }

    @Transactional
    public void saveVideoAndExerciseInfo(SaveVideoRequest saveVideoRequest,
            CustomUserDetails customUserDetails) {
        User user = userReader.getUserByEmail(customUserDetails.email());
        ExerciseSession session = sessionReader.getSession(saveVideoRequest.sessionId());
        Trial trial = trialReader.getById(saveVideoRequest.trialId());
        Video newVideo = Video.of(saveVideoRequest.vFileKey(),
                saveVideoRequest.tFileKey(), user, session, trial);
        ExerciseInfo newExerciseInfo = ExerciseInfo.of(saveVideoRequest.startedAt(),
                saveVideoRequest.endedAt(), saveVideoRequest.isSuccesses(),
                newVideo);

        videoStore.save(newVideo);
        exerciseInfoStore.save(newExerciseInfo);
    }

    // TODO 영상 삭제 추가
}
