package com.kjlee.climbmate.global.security.service;

import java.util.concurrent.TimeUnit;
import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class RedisRefreshTokenServices {

    private final StringRedisTemplate redis;
    private static final String KEY_PREFIX = "refresh:";
    private static final String BLACKLIST_PREFIX = "blacklist:access:";

    public void store(String subject, String refreshToken, long ttlMillis) {
        String key = KEY_PREFIX + subject;
        redis.opsForValue().set(key, refreshToken, ttlMillis, TimeUnit.MILLISECONDS);
    }

    public void setBlacklist(String accessToken, long ttlMillis) {
        redis.opsForValue()
                .set(BLACKLIST_PREFIX + accessToken, "1", ttlMillis, TimeUnit.MILLISECONDS);
    }

    public String get(String subject) {
        return redis.opsForValue().get(KEY_PREFIX + subject);
    }

    public void delete(String subject) {
        redis.delete(KEY_PREFIX + subject);
    }

    public boolean matches(String subject, String token) {
        String saved = get(subject);
        return saved != null && saved.equals(token);
    }

    public boolean existsInBlacklist(String accessToken) {
        return redis.hasKey(BLACKLIST_PREFIX + accessToken);
    }
}
