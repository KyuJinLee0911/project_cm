package com.ssafy.a203.domain.exerciseInfo.service;

import com.ssafy.a203.domain.exerciseInfo.entity.ExerciseInfo;
import com.ssafy.a203.domain.exerciseInfo.exception.ExerciseInfoNotFoundException;
import com.ssafy.a203.domain.exerciseInfo.repository.ExerciseInfoRepository;
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
