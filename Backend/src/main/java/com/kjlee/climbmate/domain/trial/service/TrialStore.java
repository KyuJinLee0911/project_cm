package com.kjlee.climbmate.domain.trial.service;

import com.kjlee.climbmate.domain.trial.entity.Trial;
import com.kjlee.climbmate.domain.trial.repository.TrialRespository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class TrialStore {

    private final TrialRespository trialRespository;

    public Trial save(Trial trial) {
        return trialRespository.save(trial);
    }
}
