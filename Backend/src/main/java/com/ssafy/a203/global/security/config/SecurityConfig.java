package com.ssafy.a203.global.security.config;

import com.ssafy.a203.global.security.filter.JwtAuthenticationFilter;
import com.ssafy.a203.global.security.handlers.JwtAccessDeniedHandler;
import com.ssafy.a203.global.security.handlers.JwtAuthenticationEntryPoint;
import com.ssafy.a203.global.security.service.CustomUserDetailsService;
import com.ssafy.a203.global.security.util.JwtProvider;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.authentication.ProviderManager;
import org.springframework.security.authentication.dao.DaoAuthenticationProvider;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.security.authentication.AuthenticationManager;

@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {
    private final JwtAuthenticationFilter jwtFilter;
    private final CustomUserDetailsService userDetailsService;

    private static final String[] SWAGGER_URLS = {
            "/swagger-ui/**", "/v3/api-docs/**", "/swagger-resources/**", "/webjars/**"
    };
    private static final String USER_URL = "/api/v1/users";
    private static final String LOGIN_URL = "/api/v1/auth/login";
    private static final String EMAIL_CHECK = "/api/v1/users/email";

    @Bean
    public AuthenticationManager authenticationManager() {
        DaoAuthenticationProvider provider = new DaoAuthenticationProvider();
        provider.setPasswordEncoder(passwordEncoder());
        provider.setUserDetailsService(userDetailsService);
        return new ProviderManager(provider);
    }

    @Bean
    public PasswordEncoder passwordEncoder(){
        return new BCryptPasswordEncoder();
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http, JwtProvider jwtProvider)
            throws Exception{
        http.cors(Customizer.withDefaults())
                .csrf(AbstractHttpConfigurer::disable);

        // Session 미사용
        http.sessionManagement((session) -> session.sessionCreationPolicy(
                SessionCreationPolicy.STATELESS)
        );

        // httpBasic, httpFormLogin 미사용
        http.httpBasic(AbstractHttpConfigurer::disable).formLogin(AbstractHttpConfigurer::disable);



        http.addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class);
        http.authorizeHttpRequests(auth -> auth
                .requestMatchers(SWAGGER_URLS).permitAll()
                .requestMatchers(EMAIL_CHECK).permitAll()
                .requestMatchers(HttpMethod.POST, USER_URL).permitAll()
                .requestMatchers(LOGIN_URL).permitAll()
                .requestMatchers("/error/**").permitAll()
                .anyRequest().authenticated()
        ).exceptionHandling((exceptionHandling)->
                exceptionHandling
                        .accessDeniedHandler(new JwtAccessDeniedHandler())
                        .authenticationEntryPoint(new JwtAuthenticationEntryPoint())
        );
        return http.build();
    }

}
