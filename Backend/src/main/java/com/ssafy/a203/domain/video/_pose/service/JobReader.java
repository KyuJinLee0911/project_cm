package com.ssafy.a203.domain.video._pose.service;

import com.ssafy.a203.domain.video._pose.entity.AnalyzedData;
import com.ssafy.a203.domain.video._pose.exception.DataNotFoundException;
import com.ssafy.a203.domain.video._pose.exception.JobNotFoundException;
import com.ssafy.a203.domain.video._pose.repository.JobRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class JobReader {

    private final JobRepository jobRepository;

    public AnalyzedData getById(String id) {
        return jobRepository.findByIdAndDeletedAtIsNull(id).orElseThrow(JobNotFoundException::new);
    }

    public AnalyzedData getByVideoId(Long videoId) {
        return jobRepository.findByVideoIdAndDeletedAtIsNull(videoId).orElseThrow(
                DataNotFoundException::new);
    }
}
