package com.ssafy.a203.domain.video.service;

import com.ssafy.a203.domain.video.entity.Video;
import com.ssafy.a203.domain.video.repository.VideoRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class VideoStore {

    private final VideoRepository videoRepository;

    public Video save(Video video) {
        return videoRepository.save(video);
    }
}
