package com.ssafy.a203.domain.video._hold.service;

import com.ssafy.a203.domain.video._hold.entity.Hold;
import com.ssafy.a203.domain.video._hold.repository.HoldRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class HoldStore {

    private final HoldRepository holdRepository;

    public Hold save(Hold hold) {
        return holdRepository.save(hold);
    }

    public void softDeleteByVideoId(Long videoId) {
        holdRepository.softDeleteByVideoId(videoId);
    }
}
