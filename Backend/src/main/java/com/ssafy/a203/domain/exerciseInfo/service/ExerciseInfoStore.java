package com.ssafy.a203.domain.exerciseInfo.service;

import com.ssafy.a203.domain.exerciseInfo.entity.ExerciseInfo;
import com.ssafy.a203.domain.exerciseInfo.repository.ExerciseInfoRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class ExerciseInfoStore {

    private final ExerciseInfoRepository infoRepository;

    public ExerciseInfo save(ExerciseInfo exerciseInfo) {
        return infoRepository.save(exerciseInfo);
    }

    public void softDeleteByVideoId(Long videoId) {
        infoRepository.softDeleteByVideoId(videoId);
    }
}
