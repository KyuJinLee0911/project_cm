package com.kjlee.climbmate.domain.redis.controller;

import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/test")
public class RedisTestController {

    private final StringRedisTemplate redisTemplate;

    @GetMapping("/ping")
    public String ping() {
        redisTemplate.opsForValue().set("test_key", "hello");
        return redisTemplate.opsForValue().get("test_key");
    }
}