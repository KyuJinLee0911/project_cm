package com.kjlee.climbmate.domain.user.controller;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.kjlee.climbmate.common.BaseIntegrationTest;
import com.kjlee.climbmate.domain.user.dto.request.UpdateUserRequest;
import com.kjlee.climbmate.domain.user.entity.User;
import com.kjlee.climbmate.domain.user.repository.UserRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;

@DisplayName("회원 정보 조회 및 수정 테스트")
public class UserInformationTest extends BaseIntegrationTest {

    @Autowired
    private UserRepository userRepository;

    private String token;
    @BeforeEach
    void setUp() throws Exception{
        token = authHelper.signUpAndLogin();
    }

    @Test
    @DisplayName("회원 정보 조회")
    void getUserInfo() throws Exception{
        mockMvc.perform(get("/api/v1/users")
                        .header("Authorization", "Bearer " + token))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.email").value("test@example.com"))
                .andExpect(jsonPath("$.data.nickname").value("testNickname"))
                .andExpect(jsonPath("$.data.height").value(182.5f))
                .andExpect(jsonPath("$.data.weight").value(120.2f))
                .andExpect(jsonPath("$.data.reach").value(190.3f));
    }

    @Test
    @DisplayName("회원 정보 수정")
    void setUserInfo() throws Exception{
        UpdateUserRequest request = new UpdateUserRequest("testNick2", 182.6f,
                80.7f, 300.1f);

        mockMvc.perform(put("/api/v1/users")
                        .header("Authorization", "Bearer " + token)
                    .contentType(MediaType.APPLICATION_JSON)
                    .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.data.email").value("test@example.com"))
                .andExpect(jsonPath("$.data.nickname").value("testNick2"))
                .andExpect(jsonPath("$.data.height").value(182.6f))
                .andExpect(jsonPath("$.data.weight").value(80.7f))
                .andExpect(jsonPath("$.data.reach").value(300.1f));

        User user = userRepository.findByEmailAndDeletedAtIsNull("test@example.com").orElse(null);

        assertThat(user).isNotNull();
        assertThat(user.getNickname()).isEqualTo("testNick2");
        assertThat(user.getHeight()).isEqualTo(182.6f);
        assertThat(user.getWeight()).isEqualTo(80.7f);
        assertThat(user.getReach()).isEqualTo(300.1f);
    }


}
