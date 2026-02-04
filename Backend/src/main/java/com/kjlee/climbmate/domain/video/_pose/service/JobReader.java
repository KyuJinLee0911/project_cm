package com.kjlee.climbmate.domain.video._pose.service;

import com.kjlee.climbmate.domain.video._pose.entity.AnalyzedData;
import com.kjlee.climbmate.domain.video._pose.exception.DataNotFoundException;
import com.kjlee.climbmate.domain.video._pose.exception.JobNotFoundException;
import com.kjlee.climbmate.domain.video._pose.repository.JobRepository;
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
