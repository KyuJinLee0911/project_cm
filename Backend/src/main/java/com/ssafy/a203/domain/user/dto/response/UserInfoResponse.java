package com.ssafy.a203.domain.user.dto.response;

import com.ssafy.a203.domain.user.entity.User;

public record UserInfoResponse(
        Long id,
        String email,
        String nickname,
        Float height,
        Float weight,
        Float reach
) {
    public static UserInfoResponse from(User user){
        return new UserInfoResponse(user.getId(), user.getEmail(), user.getNickname(), user.getHeight(),
                user.getWeight(), user.getReach());
    }
}
