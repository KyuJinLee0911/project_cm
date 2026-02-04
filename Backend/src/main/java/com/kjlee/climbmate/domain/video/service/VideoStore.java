package com.kjlee.climbmate.domain.video.service;

import com.kjlee.climbmate.domain.video.entity.Video;
import com.kjlee.climbmate.domain.video.repository.VideoRepository;
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
