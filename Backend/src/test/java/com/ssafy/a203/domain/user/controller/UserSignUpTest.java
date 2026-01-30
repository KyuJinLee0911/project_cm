package com.ssafy.a203.domain.user.controller;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.ssafy.a203.domain.user.dto.request.SignUpRequest;
import com.ssafy.a203.domain.user.entity.User;
import com.ssafy.a203.domain.user.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.transaction.annotation.Transactional;

@Transactional
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
public class UserSignUpTest {
    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @BeforeEach
    void setUp(){
        userRepository.deleteAll();
    }

    @Test
    @DisplayName("회원가입 및 이메일 중복 확인 테스트")
    void signUp_Success() throws Exception{
        SignUpRequest signUpRequest = new SignUpRequest("test@example.com", "password123", "testNickname",
                182.5f, 120.2f, 190.3f);

        mockMvc.perform(get("/api/v1/users/email")
                        .param("email","test@example.com"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.code").value("SUCCESS"));

        mockMvc.perform(post("/api/v1/users")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(signUpRequest)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.code").value("SUCCESS"));

        mockMvc.perform(get("/api/v1/users/email")
                        .param("email","test@example.com"))
                .andExpect(status().isBadRequest());

        User user = userRepository.findByEmailAndDeletedAtIsNull("test@example.com").orElse(null);
        assertThat(user).isNotNull();
        assertThat(user.getNickname()).isEqualTo("testNickname");
        assertThat(passwordEncoder.matches("password123", user.getPassword())).isTrue();
    }
}
