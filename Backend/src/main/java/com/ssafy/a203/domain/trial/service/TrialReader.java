package com.ssafy.a203.domain.trial.service;

import com.ssafy.a203.domain.trial.entity.Trial;
import com.ssafy.a203.domain.trial.exception.TrialNotFoundException;
import com.ssafy.a203.domain.trial.repository.TrialRespository;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class TrialReader {

    private final TrialRespository trialRespository;

    public List<Trial> getAllBySessionId(Long sessionId) {
        List<Trial> trials = trialRespository.findByExerciseSessionIdAndDeletedAtIsNull(sessionId);
        return trials;
    }

    public Trial getById(Long id) {
        return trialRespository.findByIdAndDeletedAtIsNull(id)
                .orElseThrow(TrialNotFoundException::new);
    }

}
