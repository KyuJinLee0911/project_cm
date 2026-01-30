package com.ssafy.a203.domain.exerciseSession.service;

import com.ssafy.a203.domain.exerciseInfo.service.ExerciseInfoReader;
import com.ssafy.a203.domain.exerciseInfo.service.ExerciseInfoStore;
import com.ssafy.a203.domain.exerciseSession.entity.ExerciseSession;
import com.ssafy.a203.domain.trial.entity.Trial;
import com.ssafy.a203.domain.trial.service.TrialReader;
import com.ssafy.a203.domain.trial.service.TrialStore;
import com.ssafy.a203.domain.video._hold.service.HoldReader;
import com.ssafy.a203.domain.video._hold.service.HoldStore;
import com.ssafy.a203.domain.video._pose.service.JobReader;
import com.ssafy.a203.domain.video._pose.service.JobStore;
import com.ssafy.a203.domain.video.entity.Video;
import com.ssafy.a203.domain.video.service.VideoReader;
import com.ssafy.a203.domain.video.service.VideoStore;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class ExerciseSessionDeleteService {

    private final TrialReader trialReader;
    private final TrialStore trialStore;

    private final VideoReader videoReader;
    private final VideoStore videoStore;

    private final ExerciseInfoReader exerciseInfoReader;
    private final ExerciseInfoStore exerciseInfoStore;

    private final HoldReader holdReader;
    private final HoldStore holdStore;

    private final JobReader jobReader;
    private final JobStore jobStore;

    private final ExerciseSessionReader sessionReader;
    private final ExerciseSessionStore sessionStore;

    public void deleteVideo(Long videoId) {
        exerciseInfoStore.softDeleteByVideoId(videoId);
        holdStore.softDeleteByVideoId(videoId);
        jobStore.softDeleteByVideoId(videoId);

        Video video = videoReader.getByVideoId(videoId);
        video.deleteVideo();
    }

    public void deleteTrial(Long trialId) {
        List<Video> videos = videoReader.getAllbyTrialId(trialId);
        videos.forEach(video -> deleteVideo(video.getId()));

        Trial trial = trialReader.getById(trialId);
        trial.deleteTrial();
    }

    public void deleteSession(Long sessionId) {
        List<Trial> trials = trialReader.getAllBySessionId(sessionId);
        trials.forEach(trial -> deleteTrial(trial.getId()));

        List<Video> directVideos = videoReader.getAllbySessionId(sessionId);
        directVideos.forEach(video -> deleteVideo(video.getId()));

        ExerciseSession session = sessionReader.getSession(sessionId);
        session.deleteSession();
    }
}
