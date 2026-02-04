package com.kjlee.climbmate.domain.exerciseSession.service;

import com.kjlee.climbmate.domain.exerciseSession.entity.ExerciseSession;
import com.kjlee.climbmate.domain.exerciseSession.exception.SessionNotFoundException;
import com.kjlee.climbmate.domain.exerciseSession.repository.ExerciseSessionRepository;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class ExerciseSessionReader {

    private final ExerciseSessionRepository repository;


    public List<ExerciseSession> getSessionList(Long userId) {
        return repository.findAllByUserIdAndDeletedAtIsNull(userId);
    }

    public ExerciseSession getSession(Long sessionId) {
        return repository.findByIdAndDeletedAtIsNull(sessionId).orElseThrow(
                SessionNotFoundException::new);
    }

}
