package com.kjlee.climbmate.domain.video.service;

import com.kjlee.climbmate.domain.video.dto.VideoSummaryProjection;
import com.kjlee.climbmate.domain.video.dto.response.VideoInfoResponse;
import com.kjlee.climbmate.domain.video.entity.Video;
import com.kjlee.climbmate.domain.video.exception.VideoNotFoundException;
import com.kjlee.climbmate.domain.video.repository.VideoRepository;
import java.time.LocalDate;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class VideoReader {

    private final VideoRepository videoRepository;


    public Video getByVideoId(Long videoId) {
        return videoRepository.findVideoByIdAndDeletedAtIsNull(videoId).orElseThrow();
    }

    public List<VideoInfoResponse> getAllByUserId(Long userId) {
        List<VideoInfoResponse> videos = videoRepository.findAllByUserId(userId);
        if (videos.isEmpty()) {
            throw new VideoNotFoundException();
        }

        return videos;
    }

    public List<Video> getAllbySessionId(Long sessionId) {
        return videoRepository.findAllByExerciseSessionIdAndDeletedAtIsNull(sessionId);
    }

    public List<VideoInfoResponse> getAllByDate(LocalDate date, Long userId) {
        List<VideoInfoResponse> videos = videoRepository
                .findAllByUserIdAndCreatedAtBetween(userId, date);
        if (videos.isEmpty()) {
            throw new VideoNotFoundException();
        }
        return videos;
    }

    public List<Video> getAllbyTrialId(Long trialId) {
        return videoRepository.findAllByTrialIdAndDeletedAtIsNull(trialId);
    }

    public List<VideoSummaryProjection> getSummaryByTrialId(Long trialId) {
        return videoRepository.findSummaryByTrialId(trialId);
    }
}
