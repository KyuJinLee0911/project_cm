package com.ssafy.a203.domain.user.service;

import com.ssafy.a203.domain.user.dto.request.SignUpRequest;
import com.ssafy.a203.domain.user.dto.request.UpdateUserRequest;
import com.ssafy.a203.domain.user.dto.response.UserInfoResponse;
import com.ssafy.a203.domain.user.entity.User;
import com.ssafy.a203.global.security.dto.CustomUserDetails;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class UserService {

    private final UserReader userReader;
    private final UserStore userStore;
    private final PasswordEncoder encoder;

    // 회원가입
    @Transactional
    public void signUp(SignUpRequest request){
        // 이메일 다시 중복 체크
        userReader.isExistsEmail(request.email());
        String password = encoder.encode(request.password());
        User user = User.from(request, password);
        userStore.save(user);
    }

    // 회원 정보 조회
    @Transactional(readOnly = true)
    public UserInfoResponse getUser(CustomUserDetails customUserDetails){
        User user = userReader.getUserByEmail(customUserDetails.email());
        return UserInfoResponse.from(user);
    }

    // 이메일 중복 확인
    @Transactional(readOnly = true)
    public void checkEmail(String email){
        userReader.isExistsEmail(email);
    }

    @Transactional
    // 회원 탈퇴
    public void withdraw(CustomUserDetails customUserDetails){
        User user = userReader.getUserByEmail(customUserDetails.email());
        user.withdraw();
    }

    // 회원 정보 수정
    @Transactional
    public UserInfoResponse updateUserInfo(UpdateUserRequest request, CustomUserDetails customUserDetails){
        User user = userReader.getUserByEmail(customUserDetails.email());
        user.update(request);
        return UserInfoResponse.from(user);
    }

}
