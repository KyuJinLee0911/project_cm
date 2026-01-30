package com.ssafy.a203.domain.exerciseSession.service;

import com.ssafy.a203.domain.exerciseSession.entity.ExerciseSession;
import com.ssafy.a203.domain.exerciseSession.exception.SessionNotFoundException;
import com.ssafy.a203.domain.exerciseSession.repository.ExerciseSessionRepository;
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
