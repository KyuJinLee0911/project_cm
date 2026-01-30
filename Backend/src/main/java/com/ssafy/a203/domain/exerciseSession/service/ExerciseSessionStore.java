package com.ssafy.a203.domain.exerciseSession.service;

import com.ssafy.a203.domain.exerciseSession.entity.ExerciseSession;
import com.ssafy.a203.domain.exerciseSession.repository.ExerciseSessionRepository;
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
