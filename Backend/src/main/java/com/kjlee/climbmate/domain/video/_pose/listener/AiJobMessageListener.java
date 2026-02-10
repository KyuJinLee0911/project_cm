//package com.kjlee.climbmate.domain.video._pose.listener;
//
//import com.fasterxml.jackson.databind.ObjectMapper;
//import com.kjlee.climbmate.domain.video._pose.dto.response.AiJobResponse;
//import com.kjlee.climbmate.domain.video._pose.service.AiJobService;
//import java.nio.charset.StandardCharsets;
//import lombok.RequiredArgsConstructor;
//import lombok.extern.slf4j.Slf4j;
//import org.springframework.context.annotation.Profile;
//import org.springframework.data.redis.connection.Message;
//import org.springframework.data.redis.connection.MessageListener;
//import org.springframework.stereotype.Component;
//
//@Slf4j
//@Component
//@RequiredArgsConstructor
//public class AiJobMessageListener implements MessageListener {
//
//    private final ObjectMapper objectMapper;
//    private final AiJobService aiJobService;
//
//    @Override
//    public void onMessage(Message message, byte[] pattern) {
//        try {
//
//            String body = new String(message.getBody(), StandardCharsets.UTF_8);
//            log.info(body);
//            AiJobResponse result = objectMapper.readValue(body, AiJobResponse.class);
//
//            log.info("Received AI Job Result: job_id={}, status={}",
//                    result.jobId(), result.status());
//
//            aiJobService.handleJobResult(result);
//        } catch (Exception e) {
//            log.error("failed to process Redis message", e);
//        }
//    }
//}
