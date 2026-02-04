package com.kjlee.climbmate.domain.exerciseSession.service;

import com.kjlee.climbmate.domain.exerciseSession.entity.ExerciseSession;
import com.kjlee.climbmate.domain.exerciseSession.repository.ExerciseSessionRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class ExerciseSessionStore {

    private final ExerciseSessionRepository repository;

    public ExerciseSession save(ExerciseSession session) {
        return repository.save(session);
    }
}
