package com.ssafy.a203.domain.trial.service;

import com.ssafy.a203.domain.trial.entity.Trial;
import com.ssafy.a203.domain.trial.repository.TrialRespository;
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
