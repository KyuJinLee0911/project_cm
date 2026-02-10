//package com.kjlee.climbmate.global.common.config;
//
//import com.kjlee.climbmate.domain.video._pose.listener.AiJobMessageListener;
//import lombok.RequiredArgsConstructor;
//import org.springframework.context.annotation.Bean;
//import org.springframework.context.annotation.Configuration;
//import org.springframework.context.annotation.Profile;
//import org.springframework.data.redis.connection.RedisConnectionFactory;
//import org.springframework.data.redis.listener.ChannelTopic;
//import org.springframework.data.redis.listener.RedisMessageListenerContainer;
//
//@Configuration
////@Profile("prod")
//@Profile("never")
//@RequiredArgsConstructor
//public class RedisSubscriberConfig {
//
//    private final RedisConnectionFactory connectionFactory;
//    private final AiJobMessageListener aiJobMessageListener;
//
//    @Bean
//    public RedisMessageListenerContainer redisContainer() {
//        RedisMessageListenerContainer container = new RedisMessageListenerContainer();
//        container.setConnectionFactory(connectionFactory);
//
//        container.addMessageListener(aiJobMessageListener, new ChannelTopic("ai_job_result"));
//
//        return container;
//    }
//}
