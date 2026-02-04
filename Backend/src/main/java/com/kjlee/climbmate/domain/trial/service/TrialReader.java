package com.kjlee.climbmate.domain.trial.service;

import com.kjlee.climbmate.domain.trial.entity.Trial;
import com.kjlee.climbmate.domain.trial.exception.TrialNotFoundException;
import com.kjlee.climbmate.domain.trial.repository.TrialRespository;
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
