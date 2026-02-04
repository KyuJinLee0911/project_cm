package com.kjlee.climbmate.domain.video.service;

import com.kjlee.climbmate.domain.user.exception.UnauthorizedUserException;
import com.kjlee.climbmate.domain.video._hold.dto.request.HoldDetectionRequest;
import com.kjlee.climbmate.domain.video._hold.dto.response.HoldInfoResponse;
import com.kjlee.climbmate.domain.video._hold.dto.response.SessionOpenResponse;
import com.kjlee.climbmate.domain.video._hold.entity.Hold;
import com.kjlee.climbmate.domain.video._hold.exception.SessionAlreadyExistsException;
import com.kjlee.climbmate.domain.video._hold.service.HoldService;
import com.kjlee.climbmate.domain.video.entity.Video;
import com.kjlee.climbmate.global.security.dto.CustomUserDetails;
import java.util.List;
import java.util.Objects;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

@Service
@RequiredArgsConstructor
public class AIHoldService {

    private final VideoReader videoReader;
    private final HoldService holdService;

    public SessionOpenResponse createSession(Long videoId, MultipartFile file,
            CustomUserDetails customUserDetails) {
        Video video = videoReader.getByVideoId(videoId);
        // 유저 권한 체크
        if (!video.getUser().getId().equals(customUserDetails.id())) {
            throw new UnauthorizedUserException();
        }

        if (hasSession(video)) {
            throw new SessionAlreadyExistsException();
        }
        return holdService.openSession(video, file);
    }

    public HoldInfoResponse detectHolds(HoldDetectionRequest request, Long videoId,
            boolean isEndOfDetection, CustomUserDetails customUserDetails) {
        Video video = videoReader.getByVideoId(videoId);
        // 유저 권한 체크
        if (!video.getUser().getId().equals(customUserDetails.id())) {
            throw new UnauthorizedUserException();
        }
        // 세션이 존재하고, active인 경우에만 valid. otherwise throws exception
        holdService.isSessionValid(video.getSessionId());
        // if sessions exists and valid at the sametime, send request for hold detection
        HoldInfoResponse response = holdService.detectHold(request, video);
        if (isEndOfDetection) { // if this request is last detection
            holdService.closeSession(video.getSessionId()); // close session
        }
        return response;
    }

    public void deleteHold(Long videoId, Long holdId, CustomUserDetails customUserDetails) {
        Video video = videoReader.getByVideoId(videoId);
        if (!Objects.equals(video.getUser().getId(), customUserDetails.id())) {
            throw new UnauthorizedUserException();
        }
        holdService.removeHold(video.getId(), holdId);
    }

    @Transactional
    public void removeAndCloseSession(Long videoId, CustomUserDetails customUserDetails) {
        Video video = videoReader.getByVideoId(videoId);
        if (!video.getUser().getId().equals(customUserDetails.id())) {
            throw new UnauthorizedUserException();
        }

        if (!hasSession(video)) {
            return;
        }

        // 해당 비디오의 홀드 전체 삭제
        List<Hold> holds = holdService.getHoldList(videoId);
        holds.forEach(Hold::deleteHold);

        // 영상 데이터를 불러와서 세션을 닫고
        String sessionId = video.getSessionId();
        holdService.closeSession(sessionId);

        // 영상에 있는 세션 아이디도 삭제
        video.deleteSessionId();


    }

    private boolean hasSession(Video video) {
        System.out.println(video.getSessionId());
        return !Objects.isNull(video.getSessionId()) && !video.getSessionId().isBlank();
    }
}
