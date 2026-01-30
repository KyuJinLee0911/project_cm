package com.ssafy.a203.domain.exerciseSession.service;

import com.ssafy.a203.domain.exerciseSession.dto.request.CreateSessionRequest;
import com.ssafy.a203.domain.exerciseSession.dto.response.SessionDetailResponse;
import com.ssafy.a203.domain.exerciseSession.dto.response.SessionInfoResponse;
import com.ssafy.a203.domain.exerciseSession.dto.response.SessionListResponse;
import com.ssafy.a203.domain.exerciseSession.entity.ExerciseSession;
import com.ssafy.a203.domain.exerciseSession.exception.SessionAlreadyEndedException;
import com.ssafy.a203.domain.trial.dto.response.TrialInfoResponse;
import com.ssafy.a203.domain.trial.entity.Trial;
import com.ssafy.a203.domain.trial.service.TrialReader;
import com.ssafy.a203.domain.user.entity.User;
import com.ssafy.a203.domain.user.exception.UnauthorizedUserException;
import com.ssafy.a203.domain.user.service.UserReader;
import com.ssafy.a203.global.security.dto.CustomUserDetails;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class ExerciseSessionService {

    private final ExerciseSessionReader reader;
    private final ExerciseSessionStore store;
    private final ExerciseSessionDeleteService delete;
    private final TrialReader trialReader;
    private final UserReader userReader;

    @Transactional(readOnly = true)
    public SessionDetailResponse getSessionDetail(Long sessionId,
            CustomUserDetails customUserDetails) {
        checkAuthority(sessionId, customUserDetails);
        List<Trial> trials = trialReader.getAllBySessionId(sessionId);

        List<TrialInfoResponse> trialInfoList = trials.stream()
                .map(TrialInfoResponse::from)
                .toList();
        return SessionDetailResponse.of(sessionId, trialInfoList);
    }

    @Transactional(readOnly = true)
    public SessionListResponse getSessionList(CustomUserDetails customUserDetails) {
        List<ExerciseSession> list = reader.getSessionList(customUserDetails.id());
        List<SessionInfoResponse> infoList = list.stream()
                .map(SessionInfoResponse::from)
                .toList();
        return SessionListResponse.of(infoList);
    }

    @Transactional
    public SessionInfoResponse createSession(CreateSessionRequest request,
            CustomUserDetails customUserDetails) {
        User user = userReader.getUserByEmail(customUserDetails.email());
        ExerciseSession session = ExerciseSession.from(request, user);
        store.save(session);
        return SessionInfoResponse.from(session);
    }

    @Transactional
    public SessionInfoResponse updateExerciseSession(Long sessionId,
            CustomUserDetails customUserDetails) {
        ExerciseSession session = checkAuthority(sessionId, customUserDetails);
        if (session.getEndedAt() != null) {
            throw new SessionAlreadyEndedException();
        }
        session.setEndTime();
        return SessionInfoResponse.from(session);
    }

    @Transactional
    public void deleteSession(Long sessionId, CustomUserDetails customUserDetails) {
        ExerciseSession session = checkAuthority(sessionId, customUserDetails);
        delete.deleteSession(sessionId);
    }

    private ExerciseSession checkAuthority(Long sessionId, CustomUserDetails customUserDetails) {
        ExerciseSession session = reader.getSession(sessionId);
        if (!session.getUser().getId().equals(customUserDetails.id())) {
            throw new UnauthorizedUserException();
        }
        return session;
    }

}
