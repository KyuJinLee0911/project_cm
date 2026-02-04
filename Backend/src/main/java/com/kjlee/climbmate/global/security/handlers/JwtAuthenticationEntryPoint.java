package com.kjlee.climbmate.global.security.handlers;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.kjlee.climbmate.global.common.dto.ApiResponse;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.web.AuthenticationEntryPoint;

public class JwtAuthenticationEntryPoint implements AuthenticationEntryPoint {

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Override
    public void commence(HttpServletRequest request, HttpServletResponse response,
            AuthenticationException authException) throws IOException, ServletException {
        ApiResponse<Object> res = ApiResponse.of("E1004", "인증되지 않은 사용자입니다.", null);
        String json = objectMapper.writeValueAsString(res);

        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType("application/json; charset=UTF-8");
        response.getWriter().write(String.valueOf(json));
    }
}
