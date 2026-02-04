package com.kjlee.climbmate.domain.video._pose.service;

import com.kjlee.climbmate.domain.video._pose.entity.AnalyzedData;
import com.kjlee.climbmate.domain.video._pose.repository.JobRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class JobStore {

    private final JobRepository jobRepository;

    public AnalyzedData save(AnalyzedData data) {
        return jobRepository.save(data);
    }

    public void softDeleteByVideoId(Long videoId) {
        jobRepository.softDeleteByVideoId(videoId);
    }
}
