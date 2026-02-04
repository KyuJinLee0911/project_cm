package com.kjlee.climbmate.domain.video._hold.service;

import com.kjlee.climbmate.domain.video._hold.entity.Hold;
import com.kjlee.climbmate.domain.video._hold.exception.HoldNotFoundException;
import com.kjlee.climbmate.domain.video._hold.repository.HoldRepository;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class HoldReader {

    private final HoldRepository holdRepository;

    public List<Hold> getHoldsByVideoId(Long videoId) {
        List<Hold> holds = holdRepository.findAllByVideoIdAndDeletedAtIsNull(videoId);

        return holds;
    }

    public Hold getHold(Long holdId) {
        return holdRepository.findByIdAndDeletedAtIsNull(holdId)
                .orElseThrow(HoldNotFoundException::new);
    }
}
