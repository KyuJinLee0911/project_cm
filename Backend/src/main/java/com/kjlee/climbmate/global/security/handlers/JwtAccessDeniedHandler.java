package com.kjlee.climbmate.global.security.handlers;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.kjlee.climbmate.global.common.dto.ApiResponse;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.web.access.AccessDeniedHandler;

public class JwtAccessDeniedHandler implements AccessDeniedHandler {

    private final ObjectMapper objectMapper = new ObjectMapper();
    @Override
    public void handle(HttpServletRequest request,
            HttpServletResponse response,
            AccessDeniedException accessDeniedException) throws IOException, ServletException {
        ApiResponse<Object> res = ApiResponse.of("E1003", "권한이 없는 사용자입니다.", null);
        String json = objectMapper.writeValueAsString(res);

        response.setStatus(HttpServletResponse.SC_FORBIDDEN);
        response.setContentType("application/json; charset=UTF-8");
        response.getWriter().write(String.valueOf(json));

    }
}