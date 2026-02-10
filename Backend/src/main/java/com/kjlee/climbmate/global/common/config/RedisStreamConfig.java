package com.kjlee.climbmate.global.common.config;

import com.kjlee.climbmate.domain.video._pose.listener.AiJobStreamListener;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.event.EventListener;
import org.springframework.data.redis.connection.stream.*;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.scheduling.annotation.Scheduled;

import java.time.Duration;
import java.util.List;

@Slf4j
@Configuration
@EnableScheduling
@RequiredArgsConstructor
public class RedisStreamConfig {
    private static final String STREAM_KEY = "ai_job_result_stream";
    private static final String CONSUMER_GROUP = "spring-backend-group";
    private static final String CONSUMER_NAME = "consumer-1";

    private final StringRedisTemplate redisTemplate;
    private final AiJobStreamListener listener;

    private volatile boolean ready = false;

    @EventListener(ApplicationReadyEvent.class)
    public void init() {
        createGroupIfNotExists();
        ready = true;
        log.info("✅ Redis Stream polling ready for stream: {}", STREAM_KEY);
    }

    @Scheduled(fixedDelay = 500) // 500ms마다 polling
    public void pollMessages() {
        if (!ready) return;

        try {
            log.debug("Polling stream...");
            List<MapRecord<String, Object, Object>> messages = redisTemplate.opsForStream().read(
                    Consumer.from(CONSUMER_GROUP, CONSUMER_NAME),
                    StreamReadOptions.empty()
                            .count(10)
                            .block(Duration.ofMillis(100)),
                    StreamOffset.create(STREAM_KEY, ReadOffset.lastConsumed())
            );

            if (messages != null && !messages.isEmpty()) {
                for (MapRecord<String, Object, Object> message : messages) {
                    try {
                        // Object -> String 변환
                        MapRecord<String, String, String> converted = StreamRecords.newRecord()
                                .ofStrings(convertToStringMap(message.getValue()))
                                .withStreamKey(STREAM_KEY)
                                .withId(message.getId());

                        listener.onMessage(converted);
                    } catch (Exception e) {
                        log.error("❌ Error processing message {}: {}", message.getId(), e.getMessage(), e);
                    }
                }
            }
        } catch (Exception e) {
            log.error("❌ Error polling stream: {}", e.getMessage());
        }
    }

    private java.util.Map<String, String> convertToStringMap(java.util.Map<Object, Object> map) {
        java.util.Map<String, String> result = new java.util.HashMap<>();
        map.forEach((k, v) -> result.put(k.toString(), v != null ? v.toString() : null));
        return result;
    }

    private void createGroupIfNotExists() {
        try {
            Boolean exists = redisTemplate.hasKey(STREAM_KEY);
            if (exists == null || !exists) {
                var messageId = redisTemplate.opsForStream()
                        .add(STREAM_KEY, java.util.Map.of("init", "true"));
                log.info("Stream created with init message: {}", messageId);
                if (messageId != null) {
                    redisTemplate.opsForStream().delete(STREAM_KEY, messageId);
                }
            }

            redisTemplate.opsForStream()
                    .createGroup(STREAM_KEY, ReadOffset.from("0"), CONSUMER_GROUP);
            log.info("Consumer group '{}' created", CONSUMER_GROUP);
        } catch (Exception e) {
            String message = e.getCause() != null ? e.getCause().getMessage() : e.getMessage();
            if (message != null && message.contains("BUSYGROUP")) {
                log.info("Consumer group '{}' already exists", CONSUMER_GROUP);
            } else {
                log.error("Failed to create consumer group: {}", message, e);
            }
        }
    }
}
