package com.kjlee.climbmate.domain.exerciseInfo.service;

import com.kjlee.climbmate.domain.exerciseInfo.entity.ExerciseInfo;
import com.kjlee.climbmate.domain.exerciseInfo.repository.ExerciseInfoRepository;
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
