package com.kjlee.climbmate.domain.exerciseInfo.service;

import com.kjlee.climbmate.domain.exerciseInfo.entity.ExerciseInfo;
import com.kjlee.climbmate.domain.exerciseInfo.exception.ExerciseInfoNotFoundException;
import com.kjlee.climbmate.domain.exerciseInfo.repository.ExerciseInfoRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class ExerciseInfoReader {

    private final ExerciseInfoRepository infoRepository;

    public ExerciseInfo getExerciseInfo(Long videoId) {
        return infoRepository.findByVideoIdAndDeletedAtIsNull(videoId).orElseThrow(
                ExerciseInfoNotFoundException::new);
    }
}
