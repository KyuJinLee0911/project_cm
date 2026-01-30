package com.ssafy.a203.domain.auth.controller;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.ssafy.a203.common.BaseIntegrationTest;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

public class AuthLogoutTest extends BaseIntegrationTest {

    private String token;
    @BeforeEach
    void setUp() throws Exception{
        token = authHelper.signUpAndLogin();
    }

    @Test
    @DisplayName("로그아웃 성공")
    void logoutSuccess() throws Exception{
        mockMvc.perform(post("/api/v1/auth/logout")
                .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value("SUCCESS"));

    }
}
