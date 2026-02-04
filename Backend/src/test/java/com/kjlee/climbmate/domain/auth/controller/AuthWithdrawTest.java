package com.kjlee.climbmate.domain.auth.controller;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.kjlee.climbmate.common.BaseIntegrationTest;
import com.kjlee.climbmate.domain.user.entity.User;
import com.kjlee.climbmate.domain.user.repository.UserRepository;
import java.util.Objects;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;

public class AuthWithdrawTest extends BaseIntegrationTest {

    @Autowired
    private UserRepository userRepository;
    private String token;
    @BeforeEach
    void setUp() throws Exception{
        token = authHelper.signUpAndLogin();
    }

    @Test
    @DisplayName("회원 탈퇴 테스트")
    void withdrawTest() throws Exception{
        mockMvc.perform(delete("/api/v1/users")
                .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value("SUCCESS"));

        User userAfterDeleted = userRepository.findByEmail("test@example.com").orElse(null);
        assertThat(Objects.requireNonNull(userAfterDeleted).getDeletedAt()).isNotNull();
    }

}
