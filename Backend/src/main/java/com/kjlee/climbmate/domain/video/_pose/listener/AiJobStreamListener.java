package com.kjlee.climbmate.domain.video._pose.listener;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.kjlee.climbmate.domain.video._pose.entity.AnalyzedData;
import com.kjlee.climbmate.domain.video._pose.service.JobReader;
import com.kjlee.climbmate.domain.video._pose.service.JobStore;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.connection.stream.*;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.stream.StreamListener;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Slf4j
@Service
@RequiredArgsConstructor
public class AiJobStreamListener implements StreamListener<String, MapRecord<String, String, String>> {
    private final StringRedisTemplate redisTemplate;
    private final ObjectMapper objectMapper;
    private final JobReader jobReader;
    private final JobStore jobStore;
    private final SimpMessagingTemplate messagingTemplate;

    private static final String STREAM_KEY = "ai_job_result_stream";
    private static final String CONSUMER_GROUP = "spring-backend-group";
    private static final String CONSUMER_NAME = "consumer-1";

    @Override
    public void onMessage(MapRecord<String, String, String> record){
        log.info("🔥 onMessage called: {}", record.getId());
        String messageId = record.getId().getValue();

        try {
            Map<String, String> value = record.getValue();

            String jobId = value.get("job_id");
            String eventType = value.get("eventType");
            String dataJson = value.get("data");

            log.info("Received: {} (job={}, type={})", messageId, jobId, eventType);

            JsonNode data = objectMapper.readTree(dataJson);

            switch (eventType){
                case "status":
                    handleStatusUpdate(jobId, data);
                    break;
                case "result":
                    handleResult(jobId, data);
                    break;
                case "error":
                    handleError(jobId, data);
                    break;
            }

            redisTemplate.opsForStream()
                    .acknowledge(STREAM_KEY, CONSUMER_GROUP, messageId);

            log.info("Acknowledged: {}", messageId);
        } catch (Exception e){
            log.error("Failed: {}", messageId, e);
        }
    }

    @Transactional
    protected void handleResult(String jobId, JsonNode data) {
        try {
            String status = data.get("status").asText();
            String message = data.get("message").asText();
            JsonNode result = data.get("result");

            AnalyzedData analyzedData = jobReader.getById(jobId);
            analyzedData.updateStatus(status, message);
            analyzedData.updateResult(objectMapper.writeValueAsString(result));

            jobStore.save(analyzedData);
            analyzedData.getVideo().markAsAnalyzed();

            // WebSocket으로 프론트엔드에 알림 (기존 로직 유지)
            messagingTemplate.convertAndSend(
                    "/topic/ai/jobs/" + jobId,
                    data
            );

            log.info("Result processed: job={}", jobId);
        } catch (Exception e) {
            log.error("Failed to handle result: {}", e.getMessage(), e);
            throw new RuntimeException(e);
        }
    }

    @Transactional
    protected void handleStatusUpdate(String jobId, JsonNode dataNode) {
        try {
            String status = dataNode.get("status").asText();
            String message = dataNode.get("message").asText();
            int progress = dataNode.has("progress") ? dataNode.get("progress").asInt() : 0;

            AnalyzedData analyzedData = jobReader.getById(jobId);
            analyzedData.updateStatus(status, message);
            jobStore.save(analyzedData);

            log.info("Status updated: job={}, status={}, progress={}%", jobId, status, progress);
        } catch (Exception e) {
            log.error("Failed to update status: {}", e.getMessage(), e);
            throw new RuntimeException(e);
        }
    }

    @Transactional
    protected void handleError(String jobId, JsonNode data){
        try {
            String status = data.get("status").asText();
            String message = data.get("message").asText();

            AnalyzedData analyzedData = jobReader.getById(jobId);
            analyzedData.updateStatus(status, message);
            jobStore.save(analyzedData);

            log.error("Error processed: job={}, error={}", jobId, message);
        } catch (Exception e) {
            log.error("Failed to handle error: {}", e.getMessage(), e);
            throw new RuntimeException(e);
        }
    }

    @Scheduled(fixedDelay = 600000) // 10분마다
    public void processPendingMessages() {
        try {
            PendingMessagesSummary summary = redisTemplate.opsForStream()
                    .pending(STREAM_KEY, CONSUMER_GROUP);

            long pendingCount = summary.getTotalPendingMessages();
            if (pendingCount > 0) {
                log.warn("Found {} pending messages", pendingCount);

                PendingMessages pendingMessages = redisTemplate.opsForStream()
                        .pending(STREAM_KEY, Consumer.from(CONSUMER_GROUP, CONSUMER_NAME),
                                org.springframework.data.domain.Range.unbounded(), 100);

                for (PendingMessage pm : pendingMessages) {
                    if (pm.getElapsedTimeSinceLastDelivery().toMinutes() > 10) {
                        log.info("Retrying: {}", pm.getIdAsString());

                        List<MapRecord<String, Object, Object>> claimed =
                                redisTemplate.opsForStream().claim(
                                        STREAM_KEY,
                                        CONSUMER_GROUP,
                                        CONSUMER_NAME,
                                        Duration.ofMinutes(10),
                                        RecordId.of(pm.getIdAsString())
                                );

                        for (MapRecord<String, Object, Object> raw : claimed) {
                            Map<String, String> convertedMap = raw.getValue()
                                            .entrySet()
                                                    .stream().collect(Collectors.toMap(
                                                            e-> e.getKey().toString(),
                                            e->e.getValue().toString()
                                    ));
                            MapRecord<String, String, String> message =
                                    StreamRecords.newRecord()
                                                    .ofStrings(convertedMap)
                                                            .withStreamKey(STREAM_KEY)
                                                                    .withId(raw.getId());

                            onMessage(message); // 기존 onMessage 재활용
                        }
                    }
                }
            }
        } catch (Exception e) {
            log.error("Error processing pending: {}", e.getMessage(), e);
        }
    }
}
